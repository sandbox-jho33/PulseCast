import os
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes.credentials import router as credentials_router
from .api.routes.podcast import router as podcast_router

load_dotenv()


class InMemoryRateLimiter:
    """Small per-process sliding-window limiter for public API protection."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: defaultdict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        entries = self._requests[key]
        while entries and entries[0] < cutoff:
            entries.popleft()
        if len(entries) >= self.max_requests:
            return False
        entries.append(now)
        return True


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit_key(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if auth_header:
        return f"auth:{auth_header[-32:]}"
    return f"ip:{_client_ip(request)}"


def _security_headers() -> dict[str, str]:
    return {
        "Content-Security-Policy": (
            "default-src 'self'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'"
        ),
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }


def _parse_origins() -> list[str]:
    origins = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    if os.getenv("APP_ENV", "development").lower() == "production" and "*" in origins:
        raise RuntimeError("FRONTEND_ORIGINS cannot include '*' in production")
    return origins


def create_app() -> FastAPI:
    """
    Application factory for the PulseCast FastAPI backend.

    This function is the central place to wire routers, middleware,
    and future infrastructure (DB, LangGraph, background workers, etc.).
    """
    app = FastAPI(
        title="PulseCast API",
        version="0.1.0",
        description="Backend for the PulseCast AI-generated podcast workflow.",
    )

    allowed_origins = _parse_origins()
    general_limiter = InMemoryRateLimiter(
        max_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "300")),
        window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
    )
    expensive_limiter = InMemoryRateLimiter(
        max_requests=int(os.getenv("EXPENSIVE_RATE_LIMIT_REQUESTS", "10")),
        window_seconds=int(os.getenv("EXPENSIVE_RATE_LIMIT_WINDOW_SECONDS", "60")),
    )

    @app.middleware("http")
    async def security_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path.startswith("/api/"):
            key = _rate_limit_key(request)
            limiter = (
                expensive_limiter
                if request.url.path.endswith("/generate")
                or request.url.path.endswith("/retry-audio")
                else general_limiter
            )
            if not limiter.check(key):
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests. Please wait and try again."},
                )
                for header, value in _security_headers().items():
                    response.headers.setdefault(header, value)
                return response

        response = await call_next(request)
        for header, value in _security_headers().items():
            response.headers.setdefault(header, value)
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(
        podcast_router,
        prefix="/api/v1/podcast",
        tags=["podcast"],
    )
    app.include_router(
        credentials_router,
        prefix="/api/v1/credentials",
        tags=["credentials"],
    )

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "healthy", "service": "pulsecast-api"}

    return app


app = create_app()
