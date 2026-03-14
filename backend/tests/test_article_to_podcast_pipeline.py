from __future__ import annotations

import re
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from dotenv import load_dotenv
from fastapi import BackgroundTasks
from langchain_ollama import ChatOllama

from app.api.routes import podcast as podcast_routes
from app.graph import graph as graph_module
from app.models.state import CurrentStep, DirectorDecision, GenerateRequest, JobStatus
from app.services.tts_client import TTSClient
from app.storage.repository import (
    SupabasePodcastStateRepository,
    get_repository,
    reset_repository,
)


class _DummyArticleHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        html = """
        <html>
          <head><title>Mini Dummy Article</title></head>
          <body>
            <article>
              <h1>Mini Dummy Article</h1>
              <p>Solar bees thrive in rooftop gardens and improve city harvest reliability.</p>
              <p>This article is intentionally tiny so the end-to-end test stays fast.</p>
            </article>
          </body>
        </html>
        """
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # type: ignore[override]
        return None


class TestArticleToPodcastPipeline(unittest.IsolatedAsyncioTestCase):
    persisted_job_id: str | None = None

    @classmethod
    def setUpClass(cls) -> None:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

        cls._server = ThreadingHTTPServer(("127.0.0.1", 0), _DummyArticleHandler)
        cls._thread = threading.Thread(target=cls._server.serve_forever, daemon=True)
        cls._thread.start()
        cls.article_url = f"http://127.0.0.1:{cls._server.server_port}/article"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._server.shutdown()
        cls._server.server_close()
        cls._thread.join(timeout=2)

    def setUp(self) -> None:
        reset_repository()
        graph_module._graph_runner = None

    def tearDown(self) -> None:
        graph_module._graph_runner = None
        reset_repository()

    async def test_end_to_end_real_llm_tts_and_db_persistence(self) -> None:
        repo = get_repository()
        if not isinstance(repo, SupabasePodcastStateRepository):
            self.skipTest(
                "SUPABASE_URL is not configured. Add DB credentials in backend/.env."
            )

        try:
            await repo.list_jobs(limit=1)
        except Exception as exc:
            self.fail(f"Supabase preflight failed: {type(exc).__name__}: {exc!r}")

        original_state_to_graph = graph_module._state_to_graph
        original_parse_knowledge_points = graph_module._parse_knowledge_points
        original_leo_node = graph_module.leo_node
        original_sarah_node = graph_module.sarah_node

        class _CountingLLM:
            def __init__(self) -> None:
                self.calls = 0
                self._inner = ChatOllama(
                    model="llama3.2:1b",
                    base_url="http://127.0.0.1:11434",
                    temperature=0.0,
                    request_timeout=60,
                    num_predict=96,
                )

            async def ainvoke(self, messages):  # type: ignore[no-untyped-def]
                self.calls += 1
                return await self._inner.ainvoke(messages)

        class _CountingTTSClient(TTSClient):
            synth_calls = 0

            async def synthesize(  # type: ignore[override]
                self,
                text: str,
                speaker_role: str | None = None,
                speaker: str | None = None,
                language: str = "en",
            ) -> bytes:
                _ = (speaker, language)
                type(self).synth_calls += 1
                return await super().synthesize(
                    text=text,
                    speaker_role=speaker_role,
                    speaker=speaker,
                    language=language,
                )

        llm_counter = _CountingLLM()

        def _fast_state_to_graph(state):  # type: ignore[no-untyped-def]
            graph_state = original_state_to_graph(state)
            graph_state["min_words"] = 80
            return graph_state

        def _first_knowledge_point_only(text: str) -> list[str]:
            points = original_parse_knowledge_points(text)
            return points[:1] if points else []

        def _single_pass_to_audio(state):  # type: ignore[no-untyped-def]
            _ = state
            return "audio"

        def _truncate_speaker_lines(script: str, max_words: int = 8) -> str:
            normalized_lines: list[str] = []
            seen_speakers: set[str] = set()

            for raw_line in script.split("\n"):
                match = re.match(r"^\s*(leo|sarah)\s*:\s*(.+)$", raw_line, re.IGNORECASE)
                if not match:
                    continue
                speaker = match.group(1).upper()
                text = " ".join(match.group(2).split()[:max_words]).strip()
                if not text:
                    continue
                if speaker not in seen_speakers:
                    normalized_lines.append(f"{speaker}: {text}")
                    seen_speakers.add(speaker)
                if len(seen_speakers) == 2:
                    break

            if "LEO" not in seen_speakers:
                normalized_lines.insert(0, "LEO: Quick summary of the main point.")
            if "SARAH" not in seen_speakers:
                normalized_lines.append("SARAH: Quick grounded follow-up to Leo.")

            return "\n".join(normalized_lines[:2])

        async def _short_leo_node(state):  # type: ignore[no-untyped-def]
            result = await original_leo_node(state)
            script = result.get("script")
            if isinstance(script, str):
                result["script"] = _truncate_speaker_lines(script)
            return result

        async def _short_sarah_node(state):  # type: ignore[no-untyped-def]
            result = await original_sarah_node(state)
            script = result.get("script")
            if isinstance(script, str):
                result["script"] = _truncate_speaker_lines(script)
            return result

        async def _get_fast_tts_client() -> TTSClient:
            return _CountingTTSClient(base_url="http://127.0.0.1:5002", timeout=30.0)

        background_tasks = BackgroundTasks()
        job_id: str | None = None

        with (
            patch.dict(
                "os.environ",
                {
                    "LLM_PROVIDER": "ollama",
                    "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
                    "OLLAMA_MODEL": "llama3.2:1b",
                    "TTS_SERVICE_URL": "http://127.0.0.1:5002",
                    "LLM_REQUEST_TIMEOUT": "60",
                    "NO_PROXY": "127.0.0.1,localhost",
                    "no_proxy": "127.0.0.1,localhost",
                },
                clear=False,
            ),
            patch(
                "app.graph.graph._state_to_graph",
                side_effect=_fast_state_to_graph,
            ),
            patch(
                "app.graph.graph._parse_knowledge_points",
                side_effect=_first_knowledge_point_only,
            ),
            patch(
                "app.graph.graph._should_continue",
                side_effect=_single_pass_to_audio,
            ),
            patch("app.graph.graph._get_llm", return_value=llm_counter),
            patch(
                "app.graph.graph.RESEARCHER_SYSTEM",
                "Extract 1 short bullet from the source. Output only one '- ...' line.",
            ),
            patch(
                "app.graph.graph.LEO_SYSTEM",
                "You are Leo. Reply with one concise line starting exactly with 'LEO:'.",
            ),
            patch(
                "app.graph.graph.SARAH_SYSTEM",
                "You are Sarah. Reply with one concise line starting exactly with 'SARAH:'.",
            ),
            patch(
                "app.graph.graph.DIRECTOR_SYSTEM",
                "Output APPROVE if script looks usable; otherwise CONTINUE.",
            ),
            patch("app.graph.graph.leo_node", side_effect=_short_leo_node),
            patch("app.graph.graph.sarah_node", side_effect=_short_sarah_node),
            patch(
                "app.services.tts_client.get_tts_client",
                side_effect=_get_fast_tts_client,
            ),
        ):
            response = await podcast_routes.generate_podcast(
                GenerateRequest(source_url=self.article_url),
                background_tasks,
            )
            job_id = response.job_id

            created_state = await repo.load_state(job_id)
            self.assertIsNotNone(created_state)
            assert created_state is not None
            self.assertEqual(created_state.status, JobStatus.PENDING)
            self.assertEqual(created_state.current_step, CurrentStep.INGESTING)

            for task in background_tasks.tasks:
                await task()

        final_state = await repo.load_state(job_id)
        self.assertIsNotNone(final_state)
        assert final_state is not None

        self.assertEqual(final_state.status, JobStatus.COMPLETED)
        self.assertEqual(final_state.current_step, CurrentStep.COMPLETED)
        self.assertEqual(final_state.progress_pct, 100)

        self.assertEqual(final_state.source_title, "Mini Dummy Article")
        self.assertIn("Solar bees thrive", final_state.source_markdown or "")
        self.assertTrue((final_state.knowledge_points or "").strip())
        self.assertIn("LEO:", final_state.script or "")
        self.assertIn("SARAH:", final_state.script or "")

        self.assertIn(
            final_state.director_decision,
            {DirectorDecision.APPROVE, DirectorDecision.CONTINUE},
        )
        self.assertIsNotNone(final_state.audio_segments)
        self.assertGreaterEqual(len(final_state.audio_segments or []), 2)
        self.assertTrue(
            (final_state.final_podcast_url or "").startswith(("http://", "https://"))
        )
        self.assertGreaterEqual(llm_counter.calls, 3)
        self.assertGreaterEqual(_CountingTTSClient.synth_calls, 1)

        fresh_db_repo = SupabasePodcastStateRepository()
        db_loaded_state = await fresh_db_repo.load_state(job_id)
        self.assertIsNotNone(db_loaded_state)
        assert db_loaded_state is not None
        self.assertEqual(db_loaded_state.id, job_id)
        self.assertEqual(db_loaded_state.status, JobStatus.COMPLETED)
        self.assertTrue(
            (db_loaded_state.final_podcast_url or "").startswith(("http://", "https://"))
        )

        job_ids = await fresh_db_repo.list_jobs(limit=200, search="Mini Dummy Article")
        self.assertIn(job_id, job_ids)

        TestArticleToPodcastPipeline.persisted_job_id = job_id
        print(f"Persisted DB job_id: {job_id}")
