"""
LangGraph definition of the core PulseCast dialogue loop.

This module currently exposes function and node stubs so that the FastAPI
layer and services can depend on stable interfaces. The actual LangGraph
implementation will be completed in the `graph-core` task.
"""

from __future__ import annotations

from typing import Protocol

from ..models.state import PodcastState


class PodcastGraphRunner(Protocol):
    """
    Protocol describing the minimal interface used by the API layer.

    In later tasks this may be backed by a LangGraph graph, a worker queue,
    or an in-process runner.
    """

    async def start_podcast_workflow(self, source_url: str) -> str:  # pragma: no cover - stub
        """Create a new job, persist initial state, and start the workflow."""

    async def get_podcast_state(self, job_id: str) -> PodcastState:  # pragma: no cover - stub
        """Fetch the latest state for a given job."""


async def researcher_node(state: PodcastState) -> PodcastState:
    """
    Researcher node stub.

    Extracts knowledge points from the source material and updates the state.
    """
    raise NotImplementedError("researcher_node will be implemented in graph-core task")


async def leo_node(state: PodcastState) -> PodcastState:
    """
    Leo (the visionary host) node stub.

    Consumes knowledge points and drafts or extends the script.
    """
    raise NotImplementedError("leo_node will be implemented in graph-core task")


async def sarah_node(state: PodcastState) -> PodcastState:
    """
    Sarah (the realist host) node stub.

    Reacts to Leo and further develops the script.
    """
    raise NotImplementedError("sarah_node will be implemented in graph-core task")


async def director_node(state: PodcastState) -> PodcastState:
    """
    Director node stub.

    Cleans repetition, inserts pauses, and decides whether to approve or
    request a REWRITE of the script.
    """
    raise NotImplementedError("director_node will be implemented in graph-core task")


async def start_podcast_workflow(source_url: str) -> str:
    """
    Convenience function to kick off a podcast job.

    In the full implementation this will construct or delegate to a LangGraph
    runner and return a job identifier.
    """
    raise NotImplementedError("start_podcast_workflow will be implemented in graph-core task")


async def get_podcast_state(job_id: str) -> PodcastState:
    """
    Retrieve the latest `PodcastState` for a job.

    In the full implementation this will consult the storage layer.
    """
    raise NotImplementedError("get_podcast_state will be implemented in graph-core task")

