"""
Canonical podcast state models for PulseCast.

For now this file provides a minimal placeholder `PodcastState` model and
helper functions so that other parts of the backend can depend on a stable
interface. The full schema should be aligned with `PULSECAST_SPEC.md` in a
follow-up task.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PodcastState(BaseModel):
    """
    Minimal placeholder for the podcast generation state.

    TODO:
    - Mirror the full schema defined in `PULSECAST_SPEC.md`.
    - Document field semantics and which agents may read/write them.
    """

    id: str = Field(..., description="Unique identifier for this podcast job.")
    source_url: str = Field(..., description="Original content source URL.")
    current_step: Optional[str] = Field(
        default=None,
        description="High-level step in the workflow (e.g. ingestion, script, audio).",
    )
    script: Optional[str] = Field(
        default=None,
        description="Current podcast script text. Final form will likely be structured.",
    )
    critique_count: int = Field(
        default=0,
        description="Number of times the Director has requested a REWRITE.",
    )


def new_state_from_source_url(source_url: str, job_id: str) -> PodcastState:
    """
    Initialize a new `PodcastState` from a source URL.

    The full initialization logic will be fleshed out in later tasks.
    """
    return PodcastState(id=job_id, source_url=source_url, current_step="ingestion")


def serialize_state(state: PodcastState) -> Dict[str, Any]:
    """
    Serialize the state for storage in a DB/cache layer.

    Storage-specific concerns (e.g. JSON vs. JSONB) are handled elsewhere.
    """
    return state.model_dump()


def deserialize_state(payload: Dict[str, Any]) -> PodcastState:
    """Reconstruct a `PodcastState` instance from a stored payload."""
    return PodcastState.model_validate(payload)


def increment_critique_count(state: PodcastState, *, max_critique_count: int) -> PodcastState:
    """
    Safely increment the critique counter, enforcing an upper bound.

    In the full implementation this will be used by the Director node to
    guard against infinite REWRITE loops.
    """
    if state.critique_count >= max_critique_count:
        return state

    state.critique_count += 1
    return state

