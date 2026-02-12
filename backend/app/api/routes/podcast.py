from fastapi import APIRouter, HTTPException, Path


router = APIRouter()


@router.post("/generate")
async def generate_podcast() -> None:
    """
    Trigger podcast generation workflow.

    Skeleton implementation only. The full request/response schema and
    integration with LangGraph and storage will be implemented in the
    `api-integration` task.
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/status/{job_id}")
async def get_podcast_status(
    job_id: str = Path(..., description="Podcast generation job identifier."),
) -> None:
    """
    Retrieve the latest `PodcastState` for a given job.

    Skeleton implementation only.
    """
    raise HTTPException(status_code=501, detail=f"Status for job {job_id!r} not implemented yet")


@router.get("/download/{job_id}")
async def download_podcast(
    job_id: str = Path(..., description="Podcast generation job identifier."),
) -> None:
    """
    Provide a download URL for the final synthesized podcast audio.

    Skeleton implementation only.
    """
    raise HTTPException(status_code=501, detail=f"Download for job {job_id!r} not implemented yet")


@router.patch("/edit")
async def edit_podcast() -> None:
    """
    Apply human-in-the-loop edits to the generated script.

    Skeleton implementation only.
    """
    raise HTTPException(status_code=501, detail="Edit endpoint not implemented yet")

