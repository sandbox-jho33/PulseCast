-- Store generated podcast audio in a private Supabase Storage bucket.
--
-- The backend uploads with the service role key and returns short-lived signed
-- URLs only after the authenticated user is authorized for the owning job.

INSERT INTO storage.buckets (id, name, public)
VALUES ('podcast-audio', 'podcast-audio', false)
ON CONFLICT (id) DO UPDATE
SET public = false;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'storage'
          AND tablename = 'objects'
          AND policyname = 'Service role manages podcast audio'
    ) THEN
        CREATE POLICY "Service role manages podcast audio"
            ON storage.objects
            FOR ALL
            TO service_role
            USING (bucket_id = 'podcast-audio')
            WITH CHECK (bucket_id = 'podcast-audio');
    END IF;
END $$;
