"""
Repository interfaces for persisting `PodcastState` and related artifacts.

Concrete implementations (e.g. Postgres/Supabase + Redis) will live in
separate modules and satisfy the interfaces defined here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from ..models.state import PodcastState


class PodcastStateRepository(ABC):
    """
    Abstract base class for podcast state persistence.

    Implementations may use relational storage, document storage, or caches,
    but the rest of the application should only depend on this interface.
    """

    @abstractmethod
    async def save_state(self, state: PodcastState) -> None:  # pragma: no cover - interface
        """Persist the given podcast state."""

    @abstractmethod
    async def load_state(self, job_id: str) -> PodcastState:  # pragma: no cover - interface
        """Load the latest podcast state for a job."""


class ReadOnlyPodcastStateRepository(Protocol):
    """
    Narrow protocol for components that only need read access.

    This is useful for status / download endpoints that should not mutate
    state.
    """

    async def load_state(self, job_id: str) -> PodcastState:  # pragma: no cover - protocol
        """Load the latest podcast state for a job."""

