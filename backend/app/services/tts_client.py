"""
TTS client for communicating with the XTTS v2 Docker service.

This module provides an async HTTP client to synthesize speech
from text using the XTTS v2 model running in a Docker container.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TTS_URL = os.getenv("TTS_SERVICE_URL", "http://localhost:5002")


@dataclass
class TTSServiceHealth:
    status: str
    model_loaded: bool
    device: str


@dataclass
class TTSSpeakerInfo:
    speakers: list[str]
    leo_speaker: str
    sarah_speaker: str


class TTSClient:
    """
    Async HTTP client for the TTS service.

    Usage:
        async with TTSClient() as client:
            audio_bytes = await client.synthesize("Hello!", speaker_role="leo")
    """

    def __init__(self, base_url: str = DEFAULT_TTS_URL, timeout: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "TTSClient":
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError(
                "TTSClient not initialized. Use 'async with TTSClient() as client:'"
            )
        return self._client

    async def health_check(self) -> TTSServiceHealth:
        """Check the health of the TTS service."""
        client = self._get_client()
        response = await client.get(f"{self.base_url}/health")
        response.raise_for_status()
        data = response.json()
        return TTSServiceHealth(**data)

    async def get_speakers(self) -> TTSSpeakerInfo:
        """Get available speakers from the TTS service."""
        client = self._get_client()
        response = await client.get(f"{self.base_url}/speakers")
        response.raise_for_status()
        data = response.json()
        return TTSSpeakerInfo(**data)

    async def synthesize(
        self,
        text: str,
        speaker_role: Optional[str] = None,
        speaker: Optional[str] = None,
        language: str = "en",
    ) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            speaker_role: "leo" or "sarah" (uses configured speaker for role)
            speaker: Direct speaker name (e.g., "Damien Black")
            language: Language code (default: "en")

        Returns:
            Raw WAV audio bytes
        """
        client = self._get_client()

        payload = {
            "text": text,
            "language": language,
        }

        if speaker_role:
            payload["speaker_role"] = speaker_role
        elif speaker:
            payload["speaker"] = speaker

        logger.info(
            f"Synthesizing text (len={len(text)}) with role={speaker_role or speaker}"
        )

        response = await client.post(
            f"{self.base_url}/synthesize",
            json=payload,
        )
        response.raise_for_status()

        synthesis_time = response.headers.get("X-Synthesis-Time", "unknown")
        used_speaker = response.headers.get("X-Speaker", "unknown")
        logger.info(
            f"Synthesis complete: speaker={used_speaker}, time={synthesis_time}s"
        )

        return response.content

    async def synthesize_batch(
        self,
        segments: list[dict],
    ) -> list[dict]:
        """
        Synthesize multiple text segments in batch.

        Args:
            segments: List of dicts with keys: text, speaker_role (or speaker), language

        Returns:
            List of dicts with: index, speaker, audio_base64, status (and error if failed)
        """
        client = self._get_client()

        payload = []
        for seg in segments:
            item = {"text": seg["text"], "language": seg.get("language", "en")}
            if "speaker_role" in seg:
                item["speaker_role"] = seg["speaker_role"]
            elif "speaker" in seg:
                item["speaker"] = seg["speaker"]
            payload.append(item)

        response = await client.post(
            f"{self.base_url}/synthesize/batch",
            json=payload,
        )
        response.raise_for_status()

        return response.json()


_tts_client: Optional[TTSClient] = None


async def get_tts_client() -> TTSClient:
    """
    Get or create a singleton TTS client instance.

    Note: The client must be properly closed on app shutdown.
    """
    global _tts_client
    if _tts_client is None:
        _tts_client = TTSClient()
    return _tts_client


async def close_tts_client() -> None:
    """Close the singleton TTS client."""
    global _tts_client
    if _tts_client:
        await _tts_client._client.aclose()
        _tts_client = None
