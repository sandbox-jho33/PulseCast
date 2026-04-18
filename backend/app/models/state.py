"""
Canonical podcast state models for PulseCast.

This module defines the PodcastState model that flows through the LangGraph
orchestration layer and is persisted via the repository.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CurrentStep(str, Enum):
    INGESTING = "INGESTING"
    RESEARCHING = "RESEARCHING"
    SCRIPTING = "SCRIPTING"
    DIRECTOR = "DIRECTOR"
    AUDIO = "AUDIO"
    COMPLETED = "COMPLETED"


class DirectorDecision(str, Enum):
    APPROVE = "APPROVE"
    REWRITE = "REWRITE"
    CONTINUE = "CONTINUE"


class AudioSegment(BaseModel):
    speaker: str = Field(..., description="Speaker name (LEO or SARAH)")
    text: str = Field(..., description="Text segment for TTS")
    audio_url: Optional[str] = Field(default=None, description="URL to generated audio")


class PodcastState(BaseModel):
    id: str = Field(..., description="Unique identifier for this podcast job.")
    source_url: str = Field(..., description="Original content source URL.")
    source_title: Optional[str] = Field(
        default=None, description="Title extracted from source."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Job creation timestamp."
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp."
    )

    source_markdown: Optional[str] = Field(
        default=None, description="Extracted markdown from source."
    )
    knowledge_points: Optional[str] = Field(
        default=None, description="Beat-sheet extracted by researcher."
    )
    script: Optional[str] = Field(
        default=None, description="Current podcast script with LEO:/SARAH: lines."
    )
    script_version: int = Field(default=0, description="Script revision counter.")

    status: JobStatus = Field(
        default=JobStatus.PENDING, description="Overall job status."
    )
    current_step: CurrentStep = Field(
        default=CurrentStep.INGESTING, description="Current processing step."
    )
    progress_pct: int = Field(
        default=0, ge=0, le=100, description="Progress percentage 0-100."
    )

    critique_count: int = Field(default=0, description="Number of REWRITE cycles.")
    critique_limit: int = Field(
        default=3, description="Maximum allowed REWRITE cycles."
    )

    audio_segments: Optional[List[AudioSegment]] = Field(
        default=None, description="Generated audio segments."
    )
    final_podcast_url: Optional[str] = Field(
        default=None, description="URL to final podcast audio file."
    )
    duration_seconds: Optional[float] = Field(
        default=None, description="Final podcast duration."
    )

    error_message: Optional[str] = Field(
        default=None, description="Error message if FAILED."
    )

    director_decision: Optional[DirectorDecision] = Field(
        default=None, description="Director's decision after review."
    )

    llm_provider: Optional[str] = Field(
        default=None, description="LLM provider: 'ollama', 'openai', or 'anthropic'."
    )


class PodcastStateUpdate(BaseModel):
    source_title: Optional[str] = None
    source_markdown: Optional[str] = None
    knowledge_points: Optional[str] = None
    script: Optional[str] = None
    script_version: Optional[int] = None
    status: Optional[JobStatus] = None
    current_step: Optional[CurrentStep] = None
    progress_pct: Optional[int] = None
    critique_count: Optional[int] = None
    audio_segments: Optional[List[AudioSegment]] = None
    final_podcast_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    director_decision: Optional[DirectorDecision] = None


class GenerateRequest(BaseModel):
    source_url: str = Field(
        ..., description="URL of the content to convert to podcast."
    )
    llm_provider: Optional[str] = Field(
        default=None, description="LLM provider: 'ollama', 'openai', or 'anthropic'."
    )


class GenerateResponse(BaseModel):
    job_id: str
    status: JobStatus
    current_step: CurrentStep


class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    current_step: CurrentStep
    progress_pct: int
    script_version: int
    source_title: Optional[str]
    final_podcast_url: Optional[str]
    duration_seconds: Optional[float] = None
    error_message: Optional[str]


class DownloadResponse(BaseModel):
    final_podcast_url: str
    duration_seconds: Optional[float]


class JobListItem(BaseModel):
    job_id: str
    source_url: str
    source_title: Optional[str]
    status: JobStatus
    progress_pct: int
    created_at: datetime


class JobListResponse(BaseModel):
    jobs: List[JobListItem]
    total: int


class EditRequest(BaseModel):
    job_id: str = Field(..., description="Job ID to edit.")
    script: str = Field(..., description="New script content.")
    resume_from_director: bool = Field(
        default=False, description="Resume workflow from director."
    )


class EditResponse(BaseModel):
    job_id: str
    script_version: int
    status: JobStatus


def new_state(
    job_id: str,
    source_url: str,
    llm_provider: Optional[str] = None,
) -> PodcastState:
    """Create a new PodcastState with default values."""
    return PodcastState(
        id=job_id,
        source_url=source_url,
        status=JobStatus.PENDING,
        current_step=CurrentStep.INGESTING,
        progress_pct=0,
        llm_provider=llm_provider,
    )


def apply_update(state: PodcastState, update: PodcastStateUpdate) -> PodcastState:
    """Apply partial updates to a PodcastState."""
    update_data = update.model_dump(exclude_unset=True)
    current_data = state.model_dump()
    current_data.update(update_data)
    current_data["updated_at"] = datetime.utcnow()
    return PodcastState.model_validate(current_data)


def serialize_state(state: PodcastState) -> Dict[str, Any]:
    """Serialize state for storage."""
    return state.model_dump()


def deserialize_state(payload: Dict[str, Any]) -> PodcastState:
    """Deserialize state from storage."""
    return PodcastState.model_validate(payload)
