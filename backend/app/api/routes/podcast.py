"""
Podcast API routes for PulseCast.

Endpoints:
- POST /generate: Start a new podcast generation job
- GET /jobs: List all podcast jobs
- GET /status/{job_id}: Get current status of a job
- GET /download/{job_id}: Download the final podcast
- POST /{job_id}/retry-audio: Retry only TTS/audio synthesis
- PATCH /edit: Edit the script and optionally resume
- DELETE /{job_id}: Delete a podcast job
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path as FilePath

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path
from fastapi.responses import FileResponse

from ...graph.graph import get_graph_runner
from ...models.state import (
    AudioSegment,
    CurrentStep,
    DownloadResponse,
    EditRequest,
    EditResponse,
    GenerateRequest,
    GenerateResponse,
    JobListItem,
    JobListResponse,
    JobStatus,
    PodcastState,
    StatusResponse,
    new_state,
)
from ...services.audio import get_local_audio_path, synthesize_podcast_audio
from ...services.ingestion import ingest_source
from ...services.audio import get_local_audio_path
from ...storage.repository import get_repository

router = APIRouter()


def _is_retryable_audio_state(state: PodcastState) -> bool:
    """Return True if this job can retry TTS synthesis without regenerating script."""
    has_unplayable_url = state.final_podcast_url and state.final_podcast_url.startswith(
        "file://"
    )
    failed_at_audio = (
        state.status == JobStatus.FAILED and state.current_step == CurrentStep.AUDIO
    )
    completed_without_audio = (
        state.status == JobStatus.COMPLETED
        and (not state.final_podcast_url or has_unplayable_url)
    )
    return failed_at_audio or completed_without_audio


async def _run_podcast_workflow(job_id: str) -> None:
    """Background task to run the full podcast generation workflow."""
    repo = get_repository()
    graph = get_graph_runner()

    try:
        state = await repo.load_state(job_id)
        if not state:
            return

        state.status = JobStatus.RUNNING
        state.updated_at = datetime.utcnow()
        await repo.save_state(state)

        ingestion_result = await ingest_source(state.source_url)

        state.source_title = ingestion_result.title
        state.source_markdown = ingestion_result.markdown
        state.progress_pct = 10
        state.updated_at = datetime.utcnow()
        await repo.save_state(state)

        state = await graph.run(state)
        state.updated_at = datetime.utcnow()
        await repo.save_state(state)

    except Exception as e:
        state = await repo.load_state(job_id)
        if state:
            state.status = JobStatus.FAILED
            state.error_message = str(e)
            state.updated_at = datetime.utcnow()
            await repo.save_state(state)


@router.post("/generate", response_model=GenerateResponse)
async def generate_podcast(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> GenerateResponse:
    """
    Start a new podcast generation job.

    Creates a new job, initializes state, and starts the workflow in the background.
    """
    job_id = str(uuid.uuid4())

    state = new_state(job_id, request.source_url)

    repo = get_repository()
    await repo.save_state(state)

    background_tasks.add_task(_run_podcast_workflow, job_id)

    return GenerateResponse(
        job_id=job_id,
        status=state.status,
        current_step=state.current_step,
    )


@router.get("/jobs", response_model=JobListResponse)
async def list_podcast_jobs(
    limit: int = 50,
    offset: int = 0,
    search: str = "",
) -> JobListResponse:
    """
    List all podcast generation jobs.

    Returns a paginated list of jobs ordered by creation date (newest first).
    Optional search filter matches against source_title and source_url.
    """
    repo = get_repository()
    job_ids = await repo.list_jobs(limit=limit, offset=offset, search=search)

    jobs = []
    for job_id in job_ids:
        state = await repo.load_state(job_id)
        if state:
            jobs.append(
                JobListItem(
                    job_id=state.id,
                    source_url=state.source_url,
                    source_title=state.source_title,
                    status=state.status,
                    progress_pct=state.progress_pct,
                    created_at=state.created_at,
                )
            )

    return JobListResponse(jobs=jobs, total=len(jobs))


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_podcast_status(
    job_id: str = Path(..., description="Podcast generation job identifier."),
) -> StatusResponse:
    """
    Get the current status of a podcast generation job.

    Returns status, progress, and final URL if completed.
    """
    repo = get_repository()
    state = await repo.load_state(job_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    current_step = state.current_step
    progress_pct = state.progress_pct

    if state.status == JobStatus.RUNNING and state.current_step != CurrentStep.AUDIO:
        graph = get_graph_runner()
        checkpoint_state = await graph.get_current_state(job_id)
        if checkpoint_state:
            if checkpoint_state.get("current_step"):
                try:
                    current_step = CurrentStep(checkpoint_state["current_step"])
                except ValueError:
                    pass
            if isinstance(checkpoint_state.get("progress_pct"), int):
                progress_pct = checkpoint_state["progress_pct"]

    return StatusResponse(
        job_id=state.id,
        status=state.status,
        current_step=current_step,
        progress_pct=progress_pct,
        script_version=state.script_version,
        source_title=state.source_title,
        final_podcast_url=state.final_podcast_url,
        duration_seconds=state.duration_seconds,
        error_message=state.error_message,
    )


@router.get("/download/{job_id}", response_model=DownloadResponse)
async def download_podcast(
    job_id: str = Path(..., description="Podcast generation job identifier."),
) -> DownloadResponse:
    """
    Get download URL for the final podcast.

    Returns 409 if the job is not yet completed.
    """
    repo = get_repository()
    state = await repo.load_state(job_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if state.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job {job_id} is not completed. Current status: {state.status}",
        )

    if not state.final_podcast_url:
        raise HTTPException(
            status_code=409,
            detail=f"Job {job_id} does not have a final audio URL yet",
        )

    return DownloadResponse(
        final_podcast_url=state.final_podcast_url,
        duration_seconds=state.duration_seconds,
    )


@router.get("/local-audio/{job_id}.{extension}")
async def get_local_audio(
    job_id: str = Path(..., description="Podcast generation job identifier."),
    extension: str = Path(..., description="Audio extension (mp3 or wav)."),
) -> FileResponse:
    """Serve locally generated audio files in development."""
    allowed_extensions = {"mp3": "audio/mpeg", "wav": "audio/wav"}
    if extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported audio extension")

    audio_path = FilePath(get_local_audio_path(job_id, extension))
    if not audio_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Local audio for job {job_id} not found",
        )

    return FileResponse(
        path=audio_path,
        media_type=allowed_extensions[extension],
        filename=f"{job_id}.{extension}",
    )


@router.post(
    "/{job_id}/retry-audio",
    response_model=StatusResponse,
    status_code=202,
)
async def retry_audio_synthesis(
    background_tasks: BackgroundTasks,
    job_id: str = Path(..., description="Podcast generation job identifier."),
) -> StatusResponse:
    """
    Retry TTS/audio synthesis from the existing persisted script.

    This path skips ingestion and graph script-generation nodes.
    """
    repo = get_repository()
    state = await repo.load_state(job_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if not state.script or not state.script.strip():
        raise HTTPException(
            status_code=409,
            detail=f"Job {job_id} has no script to synthesize",
        )

    if state.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=409,
            detail=f"Job {job_id} is already running",
        )

    if not _is_retryable_audio_state(state):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Job {job_id} is not in a retryable audio state "
                f"(status={state.status}, step={state.current_step})"
            ),
        )

    state.status = JobStatus.RUNNING
    state.current_step = CurrentStep.AUDIO
    state.progress_pct = 85
    state.error_message = None
    state.audio_segments = None
    state.final_podcast_url = None
    state.duration_seconds = None
    state.updated_at = datetime.utcnow()
    await repo.save_state(state)

    background_tasks.add_task(_retry_audio_workflow, job_id)

    return StatusResponse(
        job_id=state.id,
        status=state.status,
        current_step=state.current_step,
        progress_pct=state.progress_pct,
        script_version=state.script_version,
        source_title=state.source_title,
        final_podcast_url=state.final_podcast_url,
        duration_seconds=state.duration_seconds,
        error_message=state.error_message,
    )


@router.patch("/edit", response_model=EditResponse)
async def edit_podcast(
    request: EditRequest,
    background_tasks: BackgroundTasks,
) -> EditResponse:
    """
    Edit the script of a podcast job.

    Optionally resume from the director node if resume_from_director is true.
    """
    repo = get_repository()
    state = await repo.load_state(request.job_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")

    state.script = request.script
    state.script_version += 1
    state.updated_at = datetime.utcnow()
    await repo.save_state(state)

    if request.resume_from_director:
        state.status = JobStatus.RUNNING
        state.director_decision = None
        state.updated_at = datetime.utcnow()
        await repo.save_state(state)

        background_tasks.add_task(_resume_from_director, request.job_id)

    return EditResponse(
        job_id=state.id,
        script_version=state.script_version,
        status=state.status,
    )


async def _resume_from_director(job_id: str) -> None:
    """Resume workflow from the director node."""
    repo = get_repository()
    graph = get_graph_runner()

    try:
        state = await repo.load_state(job_id)
        if not state:
            return

        state = await graph.run(state)
        state.updated_at = datetime.utcnow()
        await repo.save_state(state)

    except Exception as e:
        state = await repo.load_state(job_id)
        if state:
            state.status = JobStatus.FAILED
            state.error_message = str(e)
            state.updated_at = datetime.utcnow()
            await repo.save_state(state)


async def _retry_audio_workflow(job_id: str) -> None:
    """Background task to rerun only TTS synthesis/stitch/upload for an existing job."""
    repo = get_repository()

    try:
        state = await repo.load_state(job_id)
        if not state or not state.script or not state.script.strip():
            return

        result = await synthesize_podcast_audio(state.script, job_id)
        state.audio_segments = [
            AudioSegment(
                speaker=segment.speaker,
                text=segment.text,
                audio_url=segment.audio_url,
            )
            for segment in result.segments
        ]
        state.duration_seconds = result.duration_seconds

        if result.final_url:
            state.final_podcast_url = result.final_url
            state.status = JobStatus.COMPLETED
            state.current_step = CurrentStep.COMPLETED
            state.progress_pct = 100
            state.error_message = None
        else:
            state.final_podcast_url = None
            state.status = JobStatus.FAILED
            state.current_step = CurrentStep.AUDIO
            state.progress_pct = 85
            state.error_message = (
                "Audio generation failed: no playable audio file URL was created. "
                "Check TTS and storage configuration."
            )

        state.updated_at = datetime.utcnow()
        await repo.save_state(state)

    except Exception as e:
        state = await repo.load_state(job_id)
        if state:
            state.status = JobStatus.FAILED
            state.current_step = CurrentStep.AUDIO
            state.progress_pct = 85
            state.error_message = f"Audio synthesis failed: {str(e)}"
            state.updated_at = datetime.utcnow()
            await repo.save_state(state)


@router.get("/{job_id}/script")
async def get_script(
    job_id: str = Path(..., description="Podcast generation job identifier."),
) -> dict:
    """Get the current script for a job."""
    repo = get_repository()
    state = await repo.load_state(job_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {
        "job_id": state.id,
        "script": state.script,
        "script_version": state.script_version,
        "source_title": state.source_title,
    }


@router.delete("/{job_id}", status_code=204)
async def delete_podcast(
    job_id: str = Path(..., description="Podcast generation job identifier."),
) -> None:
    """
    Delete a podcast job and all associated data.

    Removes the job record, scripts, audio segments, and audio files from storage.
    """
    repo = get_repository()
    state = await repo.load_state(job_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    await repo.delete_state(job_id)
