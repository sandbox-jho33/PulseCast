# PulseCast Deployment Checklist

## Required Services

- Clerk application for authentication.
- Supabase Postgres and Storage.
- OpenAI or Anthropic user API keys collected through the app.
- ElevenLabs user API keys collected through the app.
- Two configured ElevenLabs voice IDs for Leo and Sarah.

## Backend Environment

Set these in the backend hosting platform:

```bash
APP_ENV=production
FRONTEND_ORIGINS=https://your-frontend.example
BACKEND_PUBLIC_URL=https://your-api.example
CLERK_ISSUER=https://your-clerk-issuer
CREDENTIAL_ENCRYPTION_KEY=...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_STORAGE_BUCKET=podcast-audio
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-5-haiku-20241022
TTS_PROVIDER=elevenlabs
ELEVENLABS_LEO_VOICE_ID=...
ELEVENLABS_SARAH_VOICE_ID=...
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

Generate `CREDENTIAL_ENCRYPTION_KEY` with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Frontend Environment

```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_live_...
```

If frontend and backend are deployed separately, configure the platform or edge proxy so `/api/*` reaches the FastAPI backend. Alternatively, update `frontend/src/api/podcast.ts` to use a deployed API base URL.

## Database

Run migrations in order from `backend/migrations/`:

1. `001_initial_schema.sql`
2. `002_add_llm_provider.sql`
3. `003_auth_byok.sql`

Use a private Supabase Storage bucket where possible. If the bucket is public, generated audio URLs are public to anyone with the URL.

## CI/CD

The repository includes `.github/workflows/ci.yml` for lint, build, test, and Docker image build checks. Add deployment jobs after choosing a host such as Fly.io, Render, Railway, or ECS.
