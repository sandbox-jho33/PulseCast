-- Add llm_provider column so per-job provider selection survives the
-- background-task round-trip through Supabase.

ALTER TABLE podcast_jobs
    ADD COLUMN IF NOT EXISTS llm_provider TEXT;
