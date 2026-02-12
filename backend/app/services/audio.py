"""
Audio synthesis and post-processing interfaces for PulseCast.

This module provides stubs for ElevenLabs integration and FFmpeg-based
post-processing. The concrete logic will be implemented in the `audio-stubs`
and subsequent audio tasks.
"""

from __future__ import annotations

from typing import Any, Dict, List


async def synthesize_podcast_audio(script: str) -> Dict[str, Any]:
    """
    Synthesize podcast audio from a finalized script.

    The eventual implementation is expected to:
    - Split the script into segments / turns.
    - Call ElevenLabs (or similar) for each speaker.
    - Orchestrate FFmpeg to stitch, level, and post-process audio.
    - Return segment metadata and a final audio URL/path.
    """
    raise NotImplementedError("synthesize_podcast_audio will be implemented in the audio-stubs task")


async def list_audio_segments(job_id: str) -> List[Dict[str, Any]]:
    """
    Return metadata about generated audio segments for a job.

    This helper makes it easier for the API layer to surface granular
    audio information without exposing storage details.
    """
    raise NotImplementedError("list_audio_segments will be implemented in the audio-stubs task")

