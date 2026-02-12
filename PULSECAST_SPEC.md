## PulseCast v1.0

### 1. Identity & Vision
- **Goal**: Turn a long‑form web article into a tightly produced 2‑host podcast episode from a single `source_url`.
- **Primary users**: People who want audio versions of written content (creators, knowledge workers, teams).
- **Input**: Public `source_url`.
- **Output**: Final podcast audio file + basic metadata (title, duration, link).
- **Non‑goals v1.0**: Auth, multi‑tenant, advanced editing UI, non‑English.

### 2. System Architecture (High Level)
- **Frontend**: Next.js 15 + Tailwind + Shadcn (separate project).
- **Backend**: FastAPI app with `/api/v1/podcast/*` routes.
- **Orchestration**: LangGraph handles the script generation loop.
- **Storage**: Postgres (via Supabase or similar) for `PodcastState` + metadata.
- **Queue / async**: Redis or equivalent (v1 may stub in‑process).
- **Audio**: ElevenLabs for TTS, FFmpeg for stitching + light post‑processing, S3‑style storage for final audio.

### 3. Shared State Schema (`PodcastState`)
- **Identity**: `job_id`, `source_url`, `source_title`, `created_at`, `updated_at`.
- **Content**: `source_markdown`, `knowledge_points`, `script`, `script_version`.
- **Progress**: `status` (`PENDING|RUNNING|COMPLETED|FAILED`), `current_step` (e.g. `INGESTING`, `RESEARCHING`, `SCRIPTING`, `DIRECTOR`, `AUDIO`, `COMPLETED`), `progress_pct`.
- **Loop control**: `critique_count`, `critique_limit`.
- **Audio**: `audio_segments` (optional, coarse structure only), `final_podcast_url`, `duration_seconds`.
- **Errors**: `error_message` (optional).

### 4. Agents (Conceptual)
- **Researcher**: Reads `source_markdown` → writes `knowledge_points`. Neutral, concise, creates a beat‑sheet.
- **Leo (Visionary host)**: Uses `knowledge_points` → drafts engaging, optimistic script sections (`LEO:` lines).
- **Sarah (Realist host)**: Responds to Leo, grounds ideas, adds caveats (`SARAH:` lines).
- **Director**: Cleans repetition, enforces arc, adds `[pause: 500ms]`, chooses `APPROVE` vs `REWRITE` and updates `critique_count`.
- All agents read/write only through `PodcastState` and can be re‑run safely within the `critique_limit`.

### 5. Functional Requirements
- **FR‑01 Ingestion**: Given `source_url`, fetch HTML, convert main content to `source_markdown`, set `source_title`, persist `PodcastState`.
- **FR‑02 Script Loop**: LangGraph wires nodes `researcher → leo → sarah → director`, potentially looping `director → leo` until `APPROVE` or `critique_limit` reached.
- **FR‑03 Audio**: After approval, audio service segments the script, calls ElevenLabs, stitches with FFmpeg, uploads final file, sets `final_podcast_url`.

### 6. API Contract (FastAPI)
- **POST `/api/v1/podcast/generate`**
  - Body: `{ "source_url": string }`.
  - Creates a new job, initializes `PodcastState`, kicks off ingestion + graph (async), returns `{ job_id, status, current_step }`.
- **GET `/api/v1/podcast/status/{id}`**
  - Returns a summary view of `PodcastState` (job status, current step, progress, script_version, final_podcast_url if ready).
- **GET `/api/v1/podcast/download/{id}`**
  - Requires `status="COMPLETED"` and `final_podcast_url` set; returns `{ final_podcast_url, duration_seconds }` or a `409`‑style error if not ready.
- **PATCH `/api/v1/podcast/edit`**
  - Body (minimal v1): `{ job_id, script, resume_from_director?: bool }`.
  - Replaces `script`, bumps `script_version`, and optionally resumes from Director/audio.

### 7. UI/UX Expectations (Backend‑Facing)
- Frontend shows:
  - A simple status timeline driven by `status`, `current_step`, and `progress_pct`.
  - A source preview from `source_markdown`.
  - A player + waveform fed by `final_podcast_url` (Wavesurfer.js or similar).

### 8. Constraints & Guardrails
- Keep prompts short; downstream agents mostly see `knowledge_points` and the current script, not the full article.
- Respect token / cost budgets per node (implementation detail).
- Enforce a small `critique_limit` (e.g. 2–3 loops) to avoid infinite rewriting.
- Apply basic safety rules (avoid clearly harmful content, allow graceful failure with `status="FAILED"` and `error_message`).

### 9. Parallelization Notes
- **Ingestion** can be implemented behind `ingest_source(source_url) -> (title, markdown)` without knowing LangGraph.
- **Graph / agents** rely only on `PodcastState` and repository helpers (`load_state`, `save_state`).
- **Audio service** only requires finalized `script` and returns updated audio fields on `PodcastState`.
- **API routes** glue: they call graph/ingestion/audio services and return JSON only; no UI concerns.

### 10. Roadmap Hints (Non‑blocking)
- Future: richer editing (partial segment re‑render), personalization (different host styles/voices), playlists, and analytics.
- These should not change the basic contracts above (`PodcastState` shape + 4 core endpoints).

