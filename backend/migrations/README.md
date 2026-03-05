# Database Migrations

This directory contains SQL migration files for PulseCast.

## Running Migrations

### Option 1: Supabase Dashboard (Recommended)

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **SQL Editor**
4. Copy the contents of `001_initial_schema.sql`
5. Click **Run** to execute

### Option 2: Supabase CLI

```bash
supabase db push
```

## Migration Files

| File | Description |
|------|-------------|
| `001_initial_schema.sql` | Initial schema with podcast_jobs, scripts, and audio_segments tables |

## Storage Setup

After running migrations, create a storage bucket:

1. Go to **Storage** in Supabase Dashboard
2. Click **New bucket**
3. Name: `podcast-audio`
4. Enable **Public bucket**
5. Create

## Environment Variables

Set these in your `.env` file:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...  # From Project Settings > API > anon public
SUPABASE_SERVICE_KEY=eyJ...  # From Project Settings > API > service_role
SUPABASE_STORAGE_BUCKET=podcast-audio
```
