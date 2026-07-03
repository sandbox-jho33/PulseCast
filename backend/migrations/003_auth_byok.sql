-- Add Clerk ownership and encrypted BYOK credential storage.

ALTER TABLE podcast_jobs
    ADD COLUMN IF NOT EXISTS user_id TEXT;

UPDATE podcast_jobs
SET user_id = 'legacy-user'
WHERE user_id IS NULL;

ALTER TABLE podcast_jobs
    ALTER COLUMN user_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_podcast_jobs_user_created_at
    ON podcast_jobs(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS user_credentials (
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL CHECK (provider IN ('openai', 'anthropic', 'elevenlabs')),
    encrypted_api_key TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, provider)
);

ALTER TABLE user_credentials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access on user_credentials" ON user_credentials
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP TRIGGER IF EXISTS update_user_credentials_updated_at ON user_credentials;
CREATE TRIGGER update_user_credentials_updated_at
    BEFORE UPDATE ON user_credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
