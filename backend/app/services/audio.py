"""
Audio synthesis and post-processing for PulseCast.

This module provides TTS synthesis using the XTTS v2 service
and audio stitching with pydub.
"""

from __future__ import annotations

import io
import logging
import os
import re
import tempfile
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)
_LOCAL_AUDIO_DIR = "pulsecast"


@dataclass
class AudioSegment:
    speaker: str
    text: str
    audio_url: Optional[str] = None
    audio_bytes: Optional[bytes] = None


@dataclass
class AudioResult:
    segments: List[AudioSegment]
    final_url: Optional[str]
    duration_seconds: float


def parse_script_to_segments(script: str) -> List[AudioSegment]:
    """
    Parse a script into speaker segments.

    Expects lines like:
        LEO: Hello and welcome!
        SARAH: Thanks for having me.
        [pause: 500ms]
    """
    segments = []
    lines = script.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        pause_match = re.match(r"\[pause:\s*(\d+)ms\]", line, re.IGNORECASE)
        if pause_match:
            segments.append(
                AudioSegment(speaker="PAUSE", text=f"[{pause_match.group(1)}ms]")
            )
            continue

        speaker_match = re.match(r"(LEO|SARAH)\s*:\s*(.+)", line, re.IGNORECASE)
        if speaker_match:
            speaker = speaker_match.group(1).upper()
            text = speaker_match.group(2).strip()
            segments.append(AudioSegment(speaker=speaker, text=text))

    return segments


async def upload_audio_to_storage(
    audio_data: bytes,
    file_path: str,
    content_type: str = "audio/mpeg",
) -> Optional[str]:
    """
    Upload audio data to Supabase Storage.

    Args:
        audio_data: Raw audio bytes
        file_path: Path within the bucket (e.g., "{job_id}/final.mp3")
        content_type: MIME type of the audio

    Returns:
        Public URL of the uploaded file, or None if upload failed
    """
    if not os.getenv("SUPABASE_URL"):
        return None

    try:
        from ..storage.supabase_client import (
            get_supabase_client,
            get_storage_bucket_name,
        )

        client = get_supabase_client()
        bucket = get_storage_bucket_name()

        client.storage.from_(bucket).upload(
            file_path,
            audio_data,
            {"content-type": content_type},
        )

        public_url = client.storage.from_(bucket).get_public_url(file_path)
        return public_url

    except Exception as e:
        logger.error(f"Failed to upload audio to storage: {e}")
        return None


async def synthesize_segment(
    text: str,
    speaker: str,
) -> Optional[bytes]:
    """
    Synthesize a single text segment using the TTS service.

    Args:
        text: Text to synthesize
        speaker: Speaker name (LEO or SARAH)

    Returns:
        Raw WAV audio bytes, or None if synthesis failed
    """
    from .tts_client import get_tts_client

    speaker_role = speaker.lower()
    if speaker_role not in ("leo", "sarah"):
        logger.warning(f"Unknown speaker: {speaker}, defaulting to leo")
        speaker_role = "leo"

    try:
        client = await get_tts_client()
        async with client:
            audio_bytes = await client.synthesize(
                text=text,
                speaker_role=speaker_role,
                language="en",
            )
        return audio_bytes
    except Exception as e:
        logger.error(f"TTS synthesis failed for segment: {e}")
        return None


def stitch_audio_with_pydub(
    segments: List[AudioSegment],
    pause_ms: int = 500,
) -> bytes:
    """
    Stitch audio segments together with pauses using pydub.

    Args:
        segments: List of AudioSegment objects with audio_bytes populated
        pause_ms: Pause duration in milliseconds between segments

    Returns:
        Combined audio bytes (MP3 format)
    """
    try:
        from pydub import AudioSegment as PydubAudioSegment
        from pydub.generators import WhiteNoise
    except ImportError:
        logger.error("pydub not installed. Install with: pip install pydub")
        raise RuntimeError("pydub is required for audio stitching")

    combined = PydubAudioSegment.empty()
    silence = PydubAudioSegment.silent(duration=pause_ms)

    for i, segment in enumerate(segments):
        if segment.speaker == "PAUSE":
            pause_match = re.match(r"\[(\d+)ms\]", segment.text)
            if pause_match:
                pause_duration = int(pause_match.group(1))
                combined += PydubAudioSegment.silent(duration=pause_duration)
            continue

        if segment.audio_bytes:
            try:
                audio = PydubAudioSegment.from_wav(io.BytesIO(segment.audio_bytes))
                combined += audio
                combined += silence
            except Exception as e:
                logger.warning(f"Failed to add segment {i}: {e}")

    buffer = io.BytesIO()
    combined.export(buffer, format="mp3", bitrate="128k")
    buffer.seek(0)
    return buffer.read()


def get_local_audio_path(job_id: str, extension: str = "mp3") -> str:
    """Return canonical local audio path for a job."""
    output_dir = os.path.join(tempfile.gettempdir(), _LOCAL_AUDIO_DIR)
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, f"{job_id}.{extension}")


def get_local_audio_url(job_id: str, extension: str = "mp3") -> str:
    """Return browser-playable API URL for a locally saved audio file."""
    backend_public_url = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000").rstrip(
        "/"
    )
    return f"{backend_public_url}/api/v1/podcast/local-audio/{job_id}.{extension}"


def save_audio_locally(
    audio_bytes: bytes,
    job_id: str,
    extension: str = "mp3",
) -> str:
    """
    Save audio to a local file for development.

    Args:
        audio_bytes: Raw audio bytes
        job_id: Job ID for filename

    Returns:
        Path to the saved file
    """
    output_path = get_local_audio_path(job_id, extension)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    logger.info(f"Saved audio to: {output_path}")
    return output_path


async def synthesize_podcast_audio(script: str, job_id: str) -> AudioResult:
    """
    Synthesize podcast audio from script.

    This function:
    - Parses the script into segments
    - Calls TTS for each speaking segment
    - Stitches segments with pauses
    - Uploads to storage (if configured) or saves locally

    Args:
        script: The podcast script with LEO:/SARAH: lines
        job_id: Job ID for tracking and storage

    Returns:
        AudioResult with segments, final URL, and duration
    """
    logger.info(f"Starting audio synthesis for job {job_id}")

    segments = parse_script_to_segments(script)
    speaking_segments = [s for s in segments if s.speaker != "PAUSE"]

    logger.info(f"Found {len(speaking_segments)} speaking segments")
    if not speaking_segments:
        logger.warning(
            "No speaker-labeled segments parsed for job %s. "
            "Expected lines like 'LEO: ...' or 'SARAH: ...'.",
            job_id,
        )

    for segment in speaking_segments:
        audio_bytes = await synthesize_segment(segment.text, segment.speaker)
        segment.audio_bytes = audio_bytes

    segments_with_audio = [s for s in speaking_segments if s.audio_bytes]
    if not segments_with_audio:
        logger.error("No segments were successfully synthesized")
        estimated_duration = (
            sum(len(s.text.split()) for s in speaking_segments) / 150.0 * 60
        )
        return AudioResult(
            segments=segments,
            final_url=None,
            duration_seconds=round(estimated_duration, 1),
        )

    try:
        final_audio = stitch_audio_with_pydub(segments)
        logger.info(f"Stitched audio: {len(final_audio)} bytes")
    except Exception as e:
        logger.error(f"Failed to stitch audio: {e}")
        final_audio = None

    final_url = None
    duration_seconds = 0.0

    if final_audio:
        if os.getenv("SUPABASE_URL"):
            file_path = f"{job_id}/podcast.mp3"
            final_url = await upload_audio_to_storage(
                final_audio, file_path, "audio/mpeg"
            )
        else:
            save_audio_locally(final_audio, job_id, "mp3")
            final_url = get_local_audio_url(job_id, "mp3")

        try:
            from pydub import AudioSegment as PydubAudioSegment

            audio = PydubAudioSegment.from_mp3(io.BytesIO(final_audio))
            duration_seconds = len(audio) / 1000.0
        except Exception:
            duration_seconds = (
                sum(len(s.text.split()) for s in speaking_segments) / 150.0 * 60
            )

    return AudioResult(
        segments=segments,
        final_url=final_url,
        duration_seconds=round(duration_seconds, 1),
    )


async def generate_tts_audio(
    text: str, speaker: str, voice_id: Optional[str] = None
) -> Optional[bytes]:
    """
    Generate TTS audio for a text segment.

    Args:
        text: Text to synthesize
        speaker: Speaker name (LEO or SARAH)
        voice_id: Optional voice ID override (not used with XTTS)

    Returns:
        Raw audio bytes, or None if synthesis failed
    """
    return await synthesize_segment(text, speaker)


async def stitch_audio_segments(
    segments: List[bytes],
    pauses_ms: Optional[List[int]] = None,
) -> bytes:
    """
    Stitch multiple audio segments together with pauses.

    Args:
        segments: List of raw audio bytes (WAV format)
        pauses_ms: Pause durations in milliseconds between segments

    Returns:
        Combined audio bytes (MP3 format)
    """
    audio_segments = [
        AudioSegment(speaker="UNKNOWN", text="", audio_bytes=s) for s in segments
    ]
    return stitch_audio_with_pydub(audio_segments)
