from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.audio import (
    parse_script_to_segments,
    synthesize_podcast_audio,
    upload_audio_to_storage,
)


class _FakeBucket:
    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.upload_calls: list[tuple[str, bytes, dict]] = []

    def upload(self, path: str, file_data: bytes, file_options: dict) -> None:
        self.upload_calls.append((path, file_data, file_options))
        if self.failures_before_success > 0:
            self.failures_before_success -= 1
            raise RuntimeError("503 service unavailable")

    def get_public_url(self, path: str) -> str:
        return f"https://storage.example/{path}"


class _FakeStorage:
    def __init__(self, bucket: _FakeBucket) -> None:
        self._bucket = bucket

    def from_(self, _bucket_name: str) -> _FakeBucket:
        return self._bucket


class _FakeSupabaseClient:
    def __init__(self, bucket: _FakeBucket) -> None:
        self.storage = _FakeStorage(bucket)


class TestAudioService(unittest.IsolatedAsyncioTestCase):
    def test_parse_script_supports_markdown_and_lowercase_speakers(self) -> None:
        script = """
        - **leo:** Welcome back everyone.
        [PAUSE: 350ms]
        * sarah: Great to be here.
        """

        segments = parse_script_to_segments(script)

        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0].speaker, "LEO")
        self.assertEqual(segments[0].text, "Welcome back everyone.")
        self.assertEqual(segments[1].speaker, "PAUSE")
        self.assertEqual(segments[1].text, "[350ms]")
        self.assertEqual(segments[2].speaker, "SARAH")
        self.assertEqual(segments[2].text, "Great to be here.")

    def test_parse_script_falls_back_to_leo_chunks_without_labels(self) -> None:
        script = (
            "Welcome to the show about battery storage breakthroughs. "
            "Today we compare cost declines, grid reliability benefits, and adoption risks."
        )

        segments = parse_script_to_segments(script)

        self.assertGreaterEqual(len(segments), 1)
        self.assertTrue(all(segment.speaker == "LEO" for segment in segments))
        self.assertTrue(all(segment.text for segment in segments))

    async def test_upload_retries_transient_errors_and_sets_upsert(self) -> None:
        bucket = _FakeBucket(failures_before_success=2)
        client = _FakeSupabaseClient(bucket)

        with (
            patch.dict(
                "os.environ",
                {
                    "SUPABASE_URL": "https://example.supabase.co",
                    "SUPABASE_SERVICE_ROLE_KEY": "service-role-key",
                },
            ),
            patch("app.services.audio.asyncio.sleep", new=AsyncMock()),
            patch(
                "app.storage.supabase_client.get_supabase_client",
                return_value=client,
            ),
            patch(
                "app.storage.supabase_client.get_storage_bucket_name",
                return_value="podcast-audio",
            ),
        ):
            public_url = await upload_audio_to_storage(
                b"audio-bytes",
                "job-1/podcast.mp3",
                "audio/mpeg",
            )

        self.assertEqual(public_url, "https://storage.example/job-1/podcast.mp3")
        self.assertEqual(len(bucket.upload_calls), 3)
        self.assertEqual(bucket.upload_calls[0][2]["upsert"], "true")

    async def test_upload_supports_legacy_service_key_name(self) -> None:
        bucket = _FakeBucket()
        client = _FakeSupabaseClient(bucket)

        with (
            patch.dict(
                "os.environ",
                {
                    "SUPABASE_URL": "https://example.supabase.co",
                    "SUPABASE_SERVICE_KEY": "legacy-service-key",
                },
            ),
            patch(
                "app.storage.supabase_client.get_supabase_client",
                return_value=client,
            ),
            patch(
                "app.storage.supabase_client.get_storage_bucket_name",
                return_value="podcast-audio",
            ),
        ):
            public_url = await upload_audio_to_storage(
                b"audio-bytes",
                "job-legacy/podcast.mp3",
                "audio/mpeg",
            )

        self.assertEqual(public_url, "https://storage.example/job-legacy/podcast.mp3")
        self.assertEqual(len(bucket.upload_calls), 1)

    async def test_falls_back_to_local_url_when_storage_upload_returns_none(
        self,
    ) -> None:
        with (
            patch.dict("os.environ", {"SUPABASE_URL": "https://example.supabase.co"}),
            patch(
                "app.services.audio.synthesize_segment",
                new=AsyncMock(return_value=b"wav-bytes"),
            ),
            patch(
                "app.services.audio.stitch_audio_with_pydub",
                return_value=(b"podcast-bytes", "wav"),
            ),
            patch(
                "app.services.audio.upload_audio_to_storage",
                new=AsyncMock(return_value=None),
            ),
            patch("app.services.audio.save_audio_locally") as save_local_mock,
            patch(
                "app.services.audio.get_local_audio_url",
                return_value=(
                    "http://localhost:8000/api/v1/podcast/local-audio/job-1.wav"
                ),
            ),
        ):
            result = await synthesize_podcast_audio("LEO: Hello there", "job-1")

        self.assertEqual(
            result.final_url,
            "http://localhost:8000/api/v1/podcast/local-audio/job-1.wav",
        )
        save_local_mock.assert_called_once_with(b"podcast-bytes", "job-1", "wav")

    async def test_uses_storage_url_when_upload_succeeds(self) -> None:
        with (
            patch.dict("os.environ", {"SUPABASE_URL": "https://example.supabase.co"}),
            patch(
                "app.services.audio.synthesize_segment",
                new=AsyncMock(return_value=b"wav-bytes"),
            ),
            patch(
                "app.services.audio.stitch_audio_with_pydub",
                return_value=(b"podcast-bytes", "wav"),
            ),
            patch(
                "app.services.audio.upload_audio_to_storage",
                new=AsyncMock(
                    return_value="https://storage.example/job-2/podcast.wav"
                ),
            ),
            patch("app.services.audio.save_audio_locally") as save_local_mock,
        ):
            result = await synthesize_podcast_audio("LEO: Hello there", "job-2")

        self.assertEqual(
            result.final_url,
            "https://storage.example/job-2/podcast.wav",
        )
        save_local_mock.assert_not_called()
