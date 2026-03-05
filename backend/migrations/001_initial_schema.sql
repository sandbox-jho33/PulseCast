-- PulseCast Database Schema
-- Run this in Supabase SQL Editor to set up the database

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- PODCAST JOBS TABLE
-- Main job state tracking
-- =============================================================================

CREATE TABLE IF NOT EXISTS podcast_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL,
    source_title TEXT,
    source_markdown TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    current_step TEXT NOT NULL DEFAULT 'INGESTING',
    progress_pct INTEGER DEFAULT 0 CHECK (progress_pct >= 0 AND progress_pct <= 100),
    script_version INTEGER DEFAULT 0,
    critique_count INTEGER DEFAULT 0,
    critique_limit INTEGER DEFAULT 3,
    final_podcast_url TEXT,
    duration_seconds FLOAT,
    error_message TEXT,
    director_decision TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for quick status lookups
CREATE INDEX IF NOT EXISTS idx_podcast_jobs_status ON podcast_jobs(status);
CREATE INDEX IF NOT EXISTS idx_podcast_jobs_created_at ON podcast_jobs(created_at DESC);

-- =============================================================================
-- SCRIPTS TABLE
-- Stores script versions for each job (allows history)
-- =============================================================================

CREATE TABLE IF NOT EXISTS scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES podcast_jobs(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    knowledge_points TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, version)
);

CREATE INDEX IF NOT EXISTS idx_scripts_job_id ON scripts(job_id);

-- =============================================================================
-- AUDIO SEGMENTS TABLE
-- Individual TTS segments for each podcast
-- =============================================================================

CREATE TABLE IF NOT EXISTS audio_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES podcast_jobs(id) ON DELETE CASCADE,
    speaker TEXT NOT NULL,
    text TEXT NOT NULL,
    audio_url TEXT,
    sequence_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audio_segments_job_id ON audio_segments(job_id);

-- =============================================================================
-- UPDATED_AT TRIGGER
-- Automatically update updated_at column
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_podcast_jobs_updated_at ON podcast_jobs;
CREATE TRIGGER update_podcast_jobs_updated_at
    BEFORE UPDATE ON podcast_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- Enable RLS for production security
-- =============================================================================

ALTER TABLE podcast_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE audio_segments ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (for backend)
CREATE POLICY "Service role has full access on podcast_jobs" ON podcast_jobs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access on scripts" ON scripts
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access on audio_segments" ON audio_segments
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- =============================================================================
-- STORAGE BUCKET
-- Create storage bucket for podcast audio files
-- =============================================================================

-- Run this separately in Supabase Dashboard > Storage:
-- Create bucket named "podcast-audio" with public access enabled

-- Storage policies (run after creating bucket):
-- INSERT policy: Allow service role to upload
-- SELECT policy: Allow public read access (for audio playback)
