# Backend

Backend-specific setup and development commands for PulseCast. The primary project documentation lives in the root [README](../README.md).

## Quick Commands

```bash
cd backend
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload --port 8000
```

## Useful Commands

```bash
uv run python <script.py>
uv run mypy app/
uv run ruff check app/
```

## Notes

- FastAPI routes are mounted under `/api/v1/podcast`
- Without `SUPABASE_URL`, the backend uses in-memory storage
- Audio generation depends on the XTTS service configured by `TTS_SERVICE_URL`
