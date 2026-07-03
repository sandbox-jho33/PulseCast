import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.credentials import router as credentials_router
from .api.routes.podcast import router as podcast_router

load_dotenv()


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

    allowed_origins = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

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
