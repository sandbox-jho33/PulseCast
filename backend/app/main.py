from fastapi import FastAPI

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

    # Routers
    # NOTE: Route handlers are currently skeletons and will be implemented
    # in the `api-integration` task.
    app.include_router(
        podcast_router,
        prefix="/api/v1/podcast",
        tags=["podcast"],
    )

    return app


# ASGI entrypoint used by uvicorn / gunicorn.
app = create_app()

