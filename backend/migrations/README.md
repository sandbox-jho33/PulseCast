# Database Migrations

This directory contains SQL migration files for PulseCast.

## Running Migrations

### Option 1: Supabase Dashboard (Recommended)

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **SQL Editor**
4. Run each migration file in order
5. Click **Run** to execute

### Option 2: Supabase CLI

```bash
supabase db push
```

## Migration Files

| File | Description |
|------|-------------|
| `001_initial_schema.sql` | Initial schema with podcast_jobs, scripts, and audio_segments tables |
| `002_add_llm_provider.sql` | Adds per-job LLM provider persistence |
| `003_auth_byok.sql` | Adds Clerk ownership and encrypted BYOK credential storage |
| `004_private_audio_storage.sql` | Creates or updates private podcast audio storage |

## Storage Setup

Run `004_private_audio_storage.sql` to create or update the `podcast-audio`
bucket as private. Do not make this bucket public in production. The backend
uses the service role key for uploads and returns short-lived signed URLs only
after the authenticated user is authorized for the podcast job.

## Environment Variables

Set these in your `.env` file:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...  # From Project Settings > API > anon public
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # From Project Settings > API > service_role
# Optional backward-compatible alias:
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_STORAGE_BUCKET=podcast-audio
```
