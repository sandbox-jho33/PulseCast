"""
FastAPI TTS server wrapping XTTS v2 for PulseCast.

This server provides a REST API for text-to-speech synthesis
using the Coqui XTTS v2 model with built-in speakers.
"""

from __future__ import annotations

import io
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, ConfigDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BUILTIN_SPEAKERS = [
    "Ana Florence",
    "Damien Black",
    "Giovanni Rossi",
    "Isabella Vega",
    "Marcus Stone",
    "Sarah Thompson",
]

LEO_SPEAKER = os.getenv("LEO_SPEAKER", "Damien Black")
SARAH_SPEAKER = os.getenv("SARAH_SPEAKER", "Ana Florence")

_tts_model = None


class SynthesizeRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    speaker: Optional[str] = Field(
        None, description="Speaker name (e.g., 'Damien Black', 'Ana Florence')"
    )
    language: str = Field(default="en", description="Language code")
    speaker_role: Optional[str] = Field(
        None, description="Role: 'leo' or 'sarah' (overrides speaker)"
    )


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_loaded: bool
    device: str


class SpeakersResponse(BaseModel):
    speakers: list[str]
    leo_speaker: str
    sarah_speaker: str


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def load_model():
    global _tts_model

    if _tts_model is not None:
        return _tts_model

    logger.info("Loading XTTS v2 model...")
    start_time = time.time()

    from TTS.api import TTS

    device = get_device()
    _tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    _tts_model.to(device)

    elapsed = time.time() - start_time
    logger.info(f"Model loaded in {elapsed:.1f}s on {device}")

    return _tts_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load model
    load_model()
    logger.info(f"TTS Service ready. Leo: {LEO_SPEAKER}, Sarah: {SARAH_SPEAKER}")
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(title="PulseCast TTS Service", version="1.0.0", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy", model_loaded=_tts_model is not None, device=get_device()
    )


@app.get("/speakers", response_model=SpeakersResponse)
async def list_speakers():
    return SpeakersResponse(
        speakers=BUILTIN_SPEAKERS, leo_speaker=LEO_SPEAKER, sarah_speaker=SARAH_SPEAKER
    )


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """
    Synthesize speech from text.

    If speaker_role is provided ('leo' or 'sarah'), uses the configured speaker for that role.
    Otherwise uses the speaker parameter directly, or defaults to LEO_SPEAKER.
    """
    tts = load_model()

    if request.speaker_role:
        if request.speaker_role.lower() == "leo":
            speaker = LEO_SPEAKER
        elif request.speaker_role.lower() == "sarah":
            speaker = SARAH_SPEAKER
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown speaker_role: {request.speaker_role}"
            )
    else:
        speaker = request.speaker or LEO_SPEAKER

    if speaker not in BUILTIN_SPEAKERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown speaker: {speaker}. Available: {BUILTIN_SPEAKERS}",
        )

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        logger.info(f"Synthesizing: speaker={speaker}, text_len={len(request.text)}")
        start_time = time.time()

        buffer = io.BytesIO()
        tts.tts_to_file(
            text=request.text,
            speaker=speaker,
            language=request.language,
            file_path=buffer,
        )

        elapsed = time.time() - start_time
        logger.info(f"Synthesis complete in {elapsed:.1f}s")

        buffer.seek(0)
        return Response(
            content=buffer.read(),
            media_type="audio/wav",
            headers={
                "X-Synthesis-Time": f"{elapsed:.2f}",
                "X-Speaker": speaker,
            },
        )

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize/batch")
async def synthesize_batch(requests: list[SynthesizeRequest]):
    """
    Synthesize multiple text segments in batch.

    Returns a JSON array with audio data as base64 strings.
    """
    import base64

    results = []
    tts = load_model()

    for i, req in enumerate(requests):
        try:
            if req.speaker_role:
                speaker = (
                    LEO_SPEAKER if req.speaker_role.lower() == "leo" else SARAH_SPEAKER
                )
            else:
                speaker = req.speaker or LEO_SPEAKER

            buffer = io.BytesIO()
            tts.tts_to_file(
                text=req.text,
                speaker=speaker,
                language=req.language,
                file_path=buffer,
            )
            buffer.seek(0)

            results.append(
                {
                    "index": i,
                    "speaker": speaker,
                    "audio_base64": base64.b64encode(buffer.read()).decode(),
                    "status": "success",
                }
            )
        except Exception as e:
            results.append({"index": i, "status": "error", "error": str(e)})

    return results


if __name__ == "__main__":
    port = int(os.getenv("TTS_PORT", "5002"))
    uvicorn.run(app, host="0.0.0.0", port=port)
