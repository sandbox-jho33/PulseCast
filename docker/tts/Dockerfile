FROM ghcr.io/coqui-ai/tts-cpu:latest

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    python-multipart==0.0.6

WORKDIR /app

COPY tts_server.py /app/tts_server.py

RUN mkdir -p /app/output

ENV TTS_PORT=5002
ENV LEO_SPEAKER="Damien Black"
ENV SARAH_SPEAKER="Ana Florence"
ENV COQUI_TOS_AGREED=1

EXPOSE 5002

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

ENTRYPOINT ["python", "/app/tts_server.py"]
