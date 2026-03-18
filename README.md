# PulseCast

PulseCast turns a web article into a conversational podcast between two AI hosts. The application ingests an article URL, extracts the main content, generates a multi-step dialogue with LangGraph, and synthesizes the final script into audio.

This repository is a full-stack implementation with a FastAPI backend, a React frontend, optional Supabase persistence, and an XTTS-based text-to-speech service. It is designed to be usable locally for demos and development, while also supporting a more persistent setup with cloud storage.

## Features

- Convert a public article URL into a podcast generation job
- Extract article content and normalize it into markdown
- Generate a two-host conversation with a LangGraph workflow
- Review and revise the script through a director step
- Edit generated scripts and resume synthesis from the frontend
- Synthesize audio with separate host voices through XTTS v2
- Browse, search, and delete generated jobs from a library view
- Run with in-memory storage for local development or Supabase for persistence

## Architecture

### Backend

- **Framework:** FastAPI
- **Language:** Python 3.12+
- **Workflow engine:** LangGraph
- **LLM integration:** LangChain with Ollama or OpenAI chat models
- **State models:** Pydantic
- **Persistence:** In-memory repository by default, Supabase-backed repository when configured
- **Audio pipeline:** XTTS service for speech, `pydub` for stitching, optional Supabase Storage upload

### Frontend

- **Framework:** React 19
- **Language:** TypeScript 5.9
- **Build tool:** Vite 7
- **Styling:** Tailwind CSS 4
- **Routing:** React Router 7
- **Playback:** Browser audio player with waveform support dependencies in place

### Workflow

The backend runs a LangGraph pipeline with these conceptual stages:

1. `INGESTING` - fetch the source URL and extract readable content
2. `RESEARCHING` - turn source content into knowledge points
3. `SCRIPTING` - alternate between Leo and Sarah to draft the conversation
4. `DIRECTOR` - evaluate coverage and quality, then continue or approve
5. `AUDIO` - synthesize voice segments and stitch the final podcast
6. `COMPLETED` - expose the final audio URL and metadata

## Tech Stack

### Backend

- Python 3.12+
- FastAPI
- LangGraph
- LangChain Core
- LangChain Ollama
- LangChain OpenAI
- Pydantic
- httpx
- BeautifulSoup + lxml
- Supabase Python client
- pydub

### Frontend

- React 19
- TypeScript 5.9
- Vite 7
- Tailwind CSS 4
- React Router 7
- Motion

### Local AI and Audio

- Ollama for local LLM inference
- OpenAI as an alternative cloud LLM provider
- XTTS v2 running in Docker for text-to-speech

## Repository Layout

```text
.
├── backend/           # FastAPI app, LangGraph workflow, storage, tests, migrations
├── frontend/          # React app for generation flow and library UI
├── docker/tts/        # XTTS Docker image and TTS service wrapper
├── docker-compose.yml # Local XTTS service orchestration
├── PULSECAST_SPEC.md  # Older product spec; useful context but not source of truth
└── README.md          # Primary documentation for the whole repo
```

## Prerequisites

Install these before starting:

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- [`bun`](https://bun.sh/)
- [Docker](https://www.docker.com/)
- Either:
  - [Ollama](https://ollama.com/) for local inference, or
  - an OpenAI API key for cloud inference

Optional but recommended for persistence:

- A Supabase project with Postgres and Storage enabled

## Quickstart

This is the recommended local development path. It uses Ollama locally, runs XTTS in Docker, and starts the backend and frontend separately.

### 1. Install backend dependencies

```bash
cd backend
uv sync
```

### 2. Create the backend environment file

```bash
cp .env.example .env
```

If you are running the backend on your host machine, update these values in `backend/.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434
TTS_SERVICE_URL=http://localhost:5002
BACKEND_PUBLIC_URL=http://localhost:8000
```

Notes:

- The checked-in example uses `host.docker.internal` for Ollama because that is useful when the backend runs inside Docker. For the standard host-based dev flow in this repo, `http://localhost:11434` is the safer default.
- If you do not configure Supabase, the app still runs, but job state is stored in memory and is lost on backend restart.

### 3. Start Ollama and pull the default model

Install Ollama if needed, then run:

```bash
ollama serve
```

In another terminal, pull the default model used by the backend:

```bash
ollama pull llama3.2:3b
```

### 4. Start the XTTS service

From the repository root:

```bash
docker-compose up -d tts
```

The first run may take a while because the XTTS model and image layers need to download.

### 5. Start the backend

From `backend/`:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Backend health check:

```bash
curl http://localhost:8000/health
```

### 6. Start the frontend

From `frontend/`:

```bash
bun install
bun dev
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`.

### 7. Use the app

Open the frontend URL shown by Vite, usually [http://localhost:5173](http://localhost:5173), paste a public article URL, and start a generation job.

## Configuration

PulseCast reads its runtime configuration from `backend/.env`.

### Core LLM settings

| Variable | Required | Description |
| --- | --- | --- |
| `LLM_PROVIDER` | No | `ollama` or `openai`. Defaults to `ollama`. |
| `OLLAMA_MODEL` | When using Ollama | Ollama model name. Defaults to `llama3.2:3b`. |
| `OLLAMA_BASE_URL` | When using Ollama | Ollama server URL. Use `http://localhost:11434` for normal local dev. |
| `OPENAI_API_KEY` | When using OpenAI | OpenAI API key. |
| `OPENAI_MODEL` | When using OpenAI | Chat model name. Defaults to `gpt-4o-mini`. |
| `LLM_TEMPERATURE` | No | Sampling temperature. Defaults to `0.7`. |
| `LLM_REQUEST_TIMEOUT` | No | Request timeout in seconds for Ollama calls. Defaults to `120`. |

### TTS and backend URL settings

| Variable | Required | Description |
| --- | --- | --- |
| `TTS_SERVICE_URL` | Effectively yes for audio generation | XTTS service base URL. Defaults to `http://localhost:5002`. |
| `BACKEND_PUBLIC_URL` | No | Base URL used when generating browser-playable local audio links. Defaults to `http://localhost:8000`. |

### Supabase settings

| Variable | Required | Description |
| --- | --- | --- |
| `SUPABASE_URL` | No | Enables Supabase-backed persistence when set. |
| `SUPABASE_ANON_KEY` | No | Lowest-privilege fallback key. |
| `SUPABASE_SERVICE_ROLE_KEY` | Recommended for Supabase mode | Preferred key for server-side DB and storage access. |
| `SUPABASE_SERVICE_KEY` | Legacy fallback | Backward-compatible alias used by the codebase. |
| `SUPABASE_STORAGE_BUCKET` | No | Storage bucket name for podcast audio. Defaults to `podcast-audio`. |

## Running Modes

### Local Development Mode

Use this when you want the smallest setup that still produces podcasts locally.

Behavior:

- Repository falls back to in-memory job storage when `SUPABASE_URL` is unset
- Jobs disappear when the backend process restarts
- Final audio is saved locally and served by the backend from `/api/v1/podcast/local-audio/...`
- This mode still depends on the XTTS service for audio generation

Recommended config:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
TTS_SERVICE_URL=http://localhost:5002
BACKEND_PUBLIC_URL=http://localhost:8000
```

### Persistent Supabase Mode

Use this when you want persisted jobs, script versions, audio segments, and publicly accessible storage URLs.

Behavior:

- Job state is stored in Supabase Postgres
- Final audio is uploaded to Supabase Storage when upload succeeds
- Job history survives backend restarts
- Storage access works best with `SUPABASE_SERVICE_ROLE_KEY`

Minimum additional config:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=podcast-audio
```

### OpenAI Mode

Use this if you do not want to run Ollama locally.

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
TTS_SERVICE_URL=http://localhost:5002
```

The rest of the application flow remains the same.

## API Overview

The backend mounts podcast routes at `/api/v1/podcast`.

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/generate` | Create a new generation job from `source_url`. |
| `GET` | `/jobs` | List jobs with pagination and optional search. |
| `GET` | `/status/{job_id}` | Fetch job status, progress, and final audio metadata. |
| `GET` | `/download/{job_id}` | Return final audio URL and duration for completed jobs. |
| `GET` | `/{job_id}/script` | Return the latest script and source title. |
| `PATCH` | `/edit` | Save an edited script and optionally resume from the director step. |
| `POST` | `/{job_id}/retry-audio` | Retry only the TTS/audio stage from the existing script. |
| `DELETE` | `/{job_id}` | Delete a job and its persisted artifacts. |
| `GET` | `/local-audio/{job_id}.{extension}` | Development-only endpoint for locally saved audio files. |

### Example: create a job

```bash
curl -X POST http://localhost:8000/api/v1/podcast/generate \
  -H 'Content-Type: application/json' \
  -d '{"source_url":"https://example.com/article"}'
```

### Example: poll status

```bash
curl http://localhost:8000/api/v1/podcast/status/<job_id>
```

## Database and TTS Setup Appendix

### Supabase migrations

If you want persistent storage, run the SQL migration in `backend/migrations/001_initial_schema.sql`.

Recommended path:

1. Open your Supabase project dashboard.
2. Go to **SQL Editor**.
3. Paste the contents of `backend/migrations/001_initial_schema.sql`.
4. Run the migration.
5. Create a public storage bucket named `podcast-audio`.

The backend migration notes also live in `backend/migrations/README.md`.

### XTTS Docker service

The repository includes a Docker image definition under `docker/tts/` and a ready-to-run service in `docker-compose.yml`.

Start it with:

```bash
docker-compose up -d tts
```

Useful checks:

```bash
curl http://localhost:5002/health
curl http://localhost:5002/speakers
```

Default speakers:

- Leo: `Damien Black`
- Sarah: `Ana Florence`

You can override them through Docker environment variables if needed.

## Development Commands

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run python <script.py>
uv run mypy app/
uv run ruff check app/
```

### Frontend

```bash
cd frontend
bun install
bun dev
bun run build
bun run lint
```

### XTTS service

```bash
docker-compose up -d tts
docker-compose logs -f tts
docker-compose down
```

## Troubleshooting

### `bun: command not found`

Bun is required for the frontend commands in this repo. Install Bun first, then rerun `bun install` and `bun dev`.

### Ollama is not reachable

Symptoms:

- generation jobs fail during research or scripting
- backend logs show model connection errors or timeouts

Checks:

```bash
curl http://localhost:11434/api/tags
```

Make sure:

- Ollama is running via `ollama serve`
- `OLLAMA_BASE_URL` matches where Ollama is actually reachable
- the configured model has been pulled locally

### XTTS is not reachable

Symptoms:

- jobs reach `AUDIO` and fail
- retry synthesis is offered in the frontend

Checks:

```bash
curl http://localhost:5002/health
```

Make sure:

- `docker-compose up -d tts` succeeded
- `TTS_SERVICE_URL` points to the right endpoint
- the service has finished initial model loading

### Supabase is unset and jobs disappear

This is expected in local development mode. When `SUPABASE_URL` is not set, the backend uses an in-memory repository. Restarting the backend clears stored jobs.

### Audio falls back to local URLs

If Supabase upload is not configured or storage upload fails, the backend saves audio locally and returns a backend-served URL under `/api/v1/podcast/local-audio/{job_id}.{extension}`.

This is normal in local development. It only becomes a problem if:

- `BACKEND_PUBLIC_URL` is wrong
- the backend is not reachable from the browser
- you expected public cloud storage URLs but have not configured Supabase correctly

### A completed job may still need `Retry synthesis`

The frontend exposes retry synthesis when a job is marked complete or failed but does not have a browser-playable audio URL. This can happen if:

- storage upload failed after script generation finished
- an older run produced an unusable `file://` URL
- XTTS was unavailable during the original audio pass

`Retry synthesis` reuses the existing script and reruns only the audio stage.

## Testing and Current Verification Status

This repository contains backend test files under `backend/tests/`, including coverage for audio behavior and an end-to-end pipeline test harness.

Current repo reality:

- `uv run pytest` does **not** work out of the box in the current environment because `pytest` is not installed in the backend project dependencies
- `bun` was **not** available in the environment used to verify this documentation, so frontend build and lint commands could not be executed here

That means the commands documented above are accurate to the manifests and source files, but this README does not claim the repo is fully verified end-to-end in the current environment snapshot.

## Why This Project Is Interesting

PulseCast is a strong end-to-end AI product example because it combines article ingestion, LLM orchestration, structured state management, human-editable workflows, and audio generation in one system. It demonstrates more than prompt wiring: the repository shows API design, background processing, storage abstraction, frontend UX, and failure recovery around a real user-facing workflow.
