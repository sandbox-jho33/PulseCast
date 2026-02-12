"""
Application package for the PulseCast FastAPI backend.

The main FastAPI application is created in `main.py`. Subpackages:

- `api`: HTTP route definitions.
- `models`: Shared data models (e.g. `PodcastState`).
- `graph`: LangGraph orchestration of the podcast workflow.
- `services`: Integrations such as ingestion and audio synthesis.
- `storage`: Persistence and caching abstractions.
"""

