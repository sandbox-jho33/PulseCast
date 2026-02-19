# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.podcast import router as podcast_router


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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(
        podcast_router,
        prefix="/api/v1/podcast",
        tags=["podcast"],
    )

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "healthy", "service": "pulsecast-api"}

    return app


app = create_app()
