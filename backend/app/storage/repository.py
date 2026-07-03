"""
Repository interfaces for persisting `PodcastState` and related artifacts.

This module provides both an in-memory implementation for development/testing
and a Supabase-backed implementation for production.
"""

from __future__ import annotations

import os
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
    """Protocol defining podcast state and credential persistence."""

    async def save_state(self, state: PodcastState) -> None:
        """Persist the given podcast state."""
        ...

    async def load_state(
        self, job_id: str, user_id: Optional[str] = None
    ) -> Optional[PodcastState]:
        """Load the latest podcast state for a job, or None if not found."""
        ...

    async def delete_state(self, job_id: str, user_id: Optional[str] = None) -> None:
        """Remove a job's state from storage."""
        ...

    async def list_jobs(
        self,
        user_id: str = "test-user",
        limit: int = 50,
        offset: int = 0,
        search: str = "",
    ) -> List[str]:
        """List job IDs for one user, ordered by creation date."""
        ...

    async def save_user_credential(
        self, user_id: str, provider: str, encrypted_api_key: str
    ) -> None:
        """Persist encrypted BYOK credentials for a user."""
        ...

    async def load_user_credential(self, user_id: str, provider: str) -> Optional[str]:
        """Load encrypted BYOK credential for a user/provider."""
        ...

    async def list_user_credentials(self, user_id: str) -> List[dict]:
        """List configured credential providers for a user."""
        ...

    async def delete_user_credential(self, user_id: str, provider: str) -> None:
        """Delete one user credential."""
        ...


class InMemoryPodcastStateRepository:
    """In-memory implementation for development and tests."""

    def __init__(self) -> None:
        self._store: Dict[str, PodcastState] = {}
        self._credentials: Dict[tuple[str, str], dict] = {}

    async def save_state(self, state: PodcastState) -> None:
        self._store[state.id] = state

    async def load_state(
        self, job_id: str, user_id: Optional[str] = None
    ) -> Optional[PodcastState]:
        state = self._store.get(job_id)
        if state and user_id and state.user_id != user_id:
            return None
        return state

    async def delete_state(self, job_id: str, user_id: Optional[str] = None) -> None:
        state = self._store.get(job_id)
        if state and (user_id is None or state.user_id == user_id):
            self._store.pop(job_id, None)

    async def list_jobs(
        self,
        user_id: str = "test-user",
        limit: int = 50,
        offset: int = 0,
        search: str = "",
    ) -> List[str]:
        jobs = [state for state in self._store.values() if state.user_id == user_id]
        jobs = sorted(jobs, key=lambda s: s.created_at, reverse=True)
        if search:
            search_lower = search.lower()
            jobs = [
                job
                for job in jobs
                if (job.source_title and search_lower in job.source_title.lower())
                or search_lower in job.source_url.lower()
            ]
        return [job.id for job in jobs[offset : offset + limit]]

    async def save_user_credential(
        self, user_id: str, provider: str, encrypted_api_key: str
    ) -> None:
        self._credentials[(user_id, provider)] = {
            "provider": provider,
            "encrypted_api_key": encrypted_api_key,
            "updated_at": datetime.utcnow(),
        }

    async def load_user_credential(self, user_id: str, provider: str) -> Optional[str]:
        record = self._credentials.get((user_id, provider))
        return record["encrypted_api_key"] if record else None

    async def list_user_credentials(self, user_id: str) -> List[dict]:
        return [
            {"provider": provider, "updated_at": record["updated_at"]}
            for (owner, provider), record in self._credentials.items()
            if owner == user_id
        ]

    async def delete_user_credential(self, user_id: str, provider: str) -> None:
        self._credentials.pop((user_id, provider), None)


class SupabasePodcastStateRepository:
    """Supabase-backed implementation for production."""

    def __init__(self) -> None:
        from .supabase_client import get_supabase_client

        self._client = get_supabase_client()

    async def save_state(self, state: PodcastState) -> None:
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

    async def load_state(
        self, job_id: str, user_id: Optional[str] = None
    ) -> Optional[PodcastState]:
        query = self._client.table("podcast_jobs").select("*").eq("id", job_id)
        if user_id:
            query = query.eq("user_id", user_id)
        response = query.single().execute()
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

    async def delete_state(self, job_id: str, user_id: Optional[str] = None) -> None:
        try:
            from .supabase_client import get_storage_bucket_name

            bucket = get_storage_bucket_name()
            files = self._client.storage.from_(bucket).list(job_id)
            if files:
                file_paths = [f"{job_id}/{file['name']}" for file in files]
                self._client.storage.from_(bucket).remove(file_paths)
        except Exception:
            pass

        query = self._client.table("podcast_jobs").delete().eq("id", job_id)
        if user_id:
            query = query.eq("user_id", user_id)
        query.execute()

    async def list_jobs(
        self,
        user_id: str = "test-user",
        limit: int = 50,
        offset: int = 0,
        search: str = "",
    ) -> List[str]:
        query = (
            self._client.table("podcast_jobs")
            .select("id")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        if search:
            safe_search = search.replace(",", " ").replace("%", "\\%")
            query = query.or_(
                f"source_title.ilike.%{safe_search}%,source_url.ilike.%{safe_search}%"
            )
        response = query.execute()
        return [row["id"] for row in response.data]

    async def save_user_credential(
        self, user_id: str, provider: str, encrypted_api_key: str
    ) -> None:
        self._client.table("user_credentials").upsert(
            {
                "user_id": user_id,
                "provider": provider,
                "encrypted_api_key": encrypted_api_key,
                "updated_at": datetime.utcnow().isoformat(),
            },
            on_conflict="user_id,provider",
        ).execute()

    async def load_user_credential(self, user_id: str, provider: str) -> Optional[str]:
        response = (
            self._client.table("user_credentials")
            .select("encrypted_api_key")
            .eq("user_id", user_id)
            .eq("provider", provider)
            .single()
            .execute()
        )
        if not response.data:
            return None
        return response.data["encrypted_api_key"]

    async def list_user_credentials(self, user_id: str) -> List[dict]:
        response = (
            self._client.table("user_credentials")
            .select("provider,updated_at")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data or []

    async def delete_user_credential(self, user_id: str, provider: str) -> None:
        (
            self._client.table("user_credentials")
            .delete()
            .eq("user_id", user_id)
            .eq("provider", provider)
            .execute()
        )

    def _state_to_job_row(self, state: PodcastState) -> dict:
        return {
            "id": str(state.id),
            "user_id": state.user_id,
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
            "llm_provider": state.llm_provider,
            "created_at": state.created_at.isoformat() if state.created_at else None,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None,
        }

    def _job_row_to_state(self, row: dict) -> PodcastState:
        return PodcastState(
            id=row["id"],
            user_id=row["user_id"],
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
            llm_provider=row.get("llm_provider"),
            created_at=datetime.fromisoformat(row["created_at"])
            if row.get("created_at")
            else datetime.utcnow(),
            updated_at=datetime.fromisoformat(row["updated_at"])
            if row.get("updated_at")
            else datetime.utcnow(),
        )


_repository: Optional[PodcastStateRepository] = None


def get_repository() -> PodcastStateRepository:
    """Get the singleton repository instance."""
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
