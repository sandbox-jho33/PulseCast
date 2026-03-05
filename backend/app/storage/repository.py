"""
Repository interfaces for persisting `PodcastState` and related artifacts.

This module provides both an in-memory implementation for development/testing
and a Supabase-backed implementation for production.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Protocol

from ..models.state import (
    AudioSegment,
    CurrentStep,
    DirectorDecision,
    JobStatus,
    PodcastState,
)


class PodcastStateRepository(Protocol):
    """Protocol defining the repository interface for podcast state persistence."""

    async def save_state(self, state: PodcastState) -> None:
        """Persist the given podcast state."""
        ...

    async def load_state(self, job_id: str) -> Optional[PodcastState]:
        """Load the latest podcast state for a job, or None if not found."""
        ...

    async def delete_state(self, job_id: str) -> None:
        """Remove a job's state from storage."""
        ...

    async def list_jobs(self, limit: int = 50, offset: int = 0) -> List[str]:
        """List job IDs, ordered by creation date (newest first)."""
        ...


class InMemoryPodcastStateRepository:
    """
    In-memory implementation of podcast state persistence.

    For development and testing. Data is lost on restart.
    """

    def __init__(self) -> None:
        self._store: Dict[str, PodcastState] = {}

    async def save_state(self, state: PodcastState) -> None:
        """Persist the given podcast state."""
        self._store[state.id] = state

    async def load_state(self, job_id: str) -> Optional[PodcastState]:
        """Load the latest podcast state for a job, or None if not found."""
        return self._store.get(job_id)

    async def delete_state(self, job_id: str) -> None:
        """Remove a job's state from storage."""
        self._store.pop(job_id, None)

    async def list_jobs(self, limit: int = 50, offset: int = 0) -> List[str]:
        """List job IDs, ordered by creation date (newest first)."""
        jobs = sorted(
            self._store.values(),
            key=lambda s: s.created_at,
            reverse=True,
        )
        return [job.id for job in jobs[offset : offset + limit]]


class SupabasePodcastStateRepository:
    """
    Supabase-backed implementation of podcast state persistence.

    Stores podcast jobs, scripts, and audio segments in Postgres.
    Audio files are stored in Supabase Storage.
    """

    def __init__(self) -> None:
        from .supabase_client import get_supabase_client

        self._client = get_supabase_client()

    async def save_state(self, state: PodcastState) -> None:
        """Persist the given podcast state to Supabase."""
        job_data = self._state_to_job_row(state)

        self._client.table("podcast_jobs").upsert(job_data, on_conflict="id").execute()

        if state.script:
            self._client.table("scripts").upsert(
                {
                    "job_id": str(state.id),
                    "version": state.script_version,
                    "content": state.script,
                    "knowledge_points": state.knowledge_points,
                },
                on_conflict="job_id,version",
            ).execute()

        if state.audio_segments:
            self._client.table("audio_segments").delete().eq(
                "job_id", str(state.id)
            ).execute()

            segment_rows = [
                {
                    "job_id": str(state.id),
                    "speaker": seg.speaker,
                    "text": seg.text,
                    "audio_url": seg.audio_url,
                    "sequence_order": idx,
                }
                for idx, seg in enumerate(state.audio_segments)
            ]
            if segment_rows:
                self._client.table("audio_segments").insert(segment_rows).execute()

    async def load_state(self, job_id: str) -> Optional[PodcastState]:
        """Load the podcast state for a job from Supabase."""
        response = (
            self._client.table("podcast_jobs")
            .select("*")
            .eq("id", job_id)
            .single()
            .execute()
        )

        if not response.data:
            return None

        state = self._job_row_to_state(response.data)

        scripts_response = (
            self._client.table("scripts")
            .select("*")
            .eq("job_id", job_id)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        if scripts_response.data:
            latest_script = scripts_response.data[0]
            state.script = latest_script["content"]
            state.knowledge_points = latest_script.get("knowledge_points")

        segments_response = (
            self._client.table("audio_segments")
            .select("*")
            .eq("job_id", job_id)
            .order("sequence_order")
            .execute()
        )

        if segments_response.data:
            state.audio_segments = [
                AudioSegment(
                    speaker=seg["speaker"],
                    text=seg["text"],
                    audio_url=seg.get("audio_url"),
                )
                for seg in segments_response.data
            ]

        return state

    async def delete_state(self, job_id: str) -> None:
        """Remove a job and all related data from Supabase."""
        self._client.table("podcast_jobs").delete().eq("id", job_id).execute()

    async def list_jobs(self, limit: int = 50, offset: int = 0) -> List[str]:
        """List job IDs, ordered by creation date (newest first)."""
        response = (
            self._client.table("podcast_jobs")
            .select("id")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return [row["id"] for row in response.data]

    def _state_to_job_row(self, state: PodcastState) -> dict:
        """Convert PodcastState to a database row dict."""
        return {
            "id": str(state.id),
            "source_url": state.source_url,
            "source_title": state.source_title,
            "source_markdown": state.source_markdown,
            "status": state.status.value if state.status else JobStatus.PENDING.value,
            "current_step": state.current_step.value
            if state.current_step
            else CurrentStep.INGESTING.value,
            "progress_pct": state.progress_pct,
            "script_version": state.script_version,
            "critique_count": state.critique_count,
            "critique_limit": state.critique_limit,
            "final_podcast_url": state.final_podcast_url,
            "duration_seconds": state.duration_seconds,
            "error_message": state.error_message,
            "director_decision": state.director_decision.value
            if state.director_decision
            else None,
            "created_at": state.created_at.isoformat() if state.created_at else None,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None,
        }

    def _job_row_to_state(self, row: dict) -> PodcastState:
        """Convert a database row dict to PodcastState."""
        return PodcastState(
            id=row["id"],
            source_url=row["source_url"],
            source_title=row.get("source_title"),
            source_markdown=row.get("source_markdown"),
            status=JobStatus(row["status"]) if row.get("status") else JobStatus.PENDING,
            current_step=CurrentStep(row["current_step"])
            if row.get("current_step")
            else CurrentStep.INGESTING,
            progress_pct=row.get("progress_pct", 0),
            script_version=row.get("script_version", 0),
            critique_count=row.get("critique_count", 0),
            critique_limit=row.get("critique_limit", 3),
            final_podcast_url=row.get("final_podcast_url"),
            duration_seconds=row.get("duration_seconds"),
            error_message=row.get("error_message"),
            director_decision=DirectorDecision(row["director_decision"])
            if row.get("director_decision")
            else None,
            created_at=datetime.fromisoformat(row["created_at"])
            if row.get("created_at")
            else datetime.utcnow(),
            updated_at=datetime.fromisoformat(row["updated_at"])
            if row.get("updated_at")
            else datetime.utcnow(),
        )


_repository: Optional[PodcastStateRepository] = None


def get_repository() -> PodcastStateRepository:
    """
    Get the singleton repository instance.

    Returns SupabaseRepository if SUPABASE_URL is set, otherwise InMemoryRepository.
    """
    global _repository
    if _repository is None:
        if os.getenv("SUPABASE_URL"):
            _repository = SupabasePodcastStateRepository()
        else:
            _repository = InMemoryPodcastStateRepository()
    return _repository


def reset_repository() -> None:
    """Reset the repository singleton (useful for testing)."""
    global _repository
    _repository = None
