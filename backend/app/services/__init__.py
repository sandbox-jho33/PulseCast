"""
Service-layer integrations for the PulseCast backend.

This package hosts implementations for:
- Content ingestion (web pages, PDFs, raw text).
- Audio synthesis and post-processing.
- TTS client for XTTS v2 service.
"""

from .audio import AudioResult, AudioSegment, synthesize_podcast_audio
from .ingestion import IngestionResult, ingest_source
from .tts_client import TTSClient, get_tts_client, close_tts_client

__all__ = [
    "AudioResult",
    "AudioSegment",
    "IngestionResult",
    "TTSClient",
    "close_tts_client",
    "get_tts_client",
    "ingest_source",
    "synthesize_podcast_audio",
]
