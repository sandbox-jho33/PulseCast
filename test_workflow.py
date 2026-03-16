#!/usr/bin/env python
"""
Quick end-to-end test for PulseCast workflow.

Tests each component individually to identify issues quickly.
"""

import asyncio
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and return result."""
    print(f"{'=' * 60}")
    print(f"TEST: {description}")
    print(f"CMD:   {' '.join(cmd)}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(f"✅ PASS")
            return True
        else:
            print(f"❌ FAIL: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_docker():
    """Test if Docker is running."""
    return run_command(["docker", "--version"], "Docker is installed")


def test_tts_container():
    """Test if TTS container is running."""
    result = subprocess.run(
        ["docker-compose", "ps"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if "pulsecast-tts" in result.stdout:
        return run_command(
            ["curl", "-s", "http://localhost:5002/health"], "TTS health endpoint"
        )
    else:
        print(f"❌ FAIL: TTS container not running")
        return False


def test_tts_synthesis():
    """Test TTS synthesis (creates test.wav)."""
    return run_command(
        [
            "curl",
            "-X",
            "POST",
            "http://localhost:5002/synthesize",
            "-H",
            "Content-Type: application/json",
            "-d",
            '{"text": "Quick test.", "speaker_role": "leo"}',
            "--output",
            "test.wav",
            "--max-time",
            "60",
        ],
        "TTS audio synthesis (60s timeout)",
    )


def test_backend():
    """Test if backend is running on port 8000."""
    return run_command(
        ["curl", "-s", "http://localhost:8000/api/docs"], "Backend API docs endpoint"
    )


def test_frontend():
    """Test if frontend is running on port 5173."""
    return run_command(["curl", "-s", "http://localhost:5173"], "Frontend web server")


def test_ollama():
    """Test if Ollama is running on port 11434."""
    return run_command(
        ["curl", "-s", "http://localhost:11434/api/tags"], "Ollama API endpoint"
    )


async def test_end_to_end():
    """Test minimal end-to-end flow."""
    print(f"\n{'=' * 60}")
    print("E2E TEST: Create a short podcast")
    print(f"{'=' * 60}\n")

    import httpx

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8000/api/generate",
                json={"source_url": "https://example.com/test"},
            )

            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                print(f"✅ Job created: {job_id}")

                print(f"{'=' * 60}")
                print("Waiting for status updates...")
                print(f"{'=' * 60}\n")

                for i in range(5):
                    status_response = await client.get(
                        f"http://localhost:8000/api/status/{job_id}"
                    )
                    status = status_response.json()

                    print(
                        f"Step {i + 1}: {status.get('current_step', 'UNKNOWN')} "
                        f"({status.get('progress_pct', 0)}%)"
                    )

                    if status.get("status") == "COMPLETED":
                        print(f"\n✅ Job completed in {i + 1} steps!")
                        return True

                    if status.get("status") == "FAILED":
                        print(f"\n❌ Job failed: {status.get('error_message')}")
                        return False

                    await asyncio.sleep(5)

                print(f"\n⏱ Timeout after {5 * 5}s")
                return False
    except Exception as e:
        print(f"❌ E2E test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PULSECAST WORKFLOW TEST SUITE")
    print("=" * 60 + "\n")

    results = []

    tests = [
        ("Docker", test_docker),
        ("TTS Container", test_tts_container),
        ("TTS Health", test_tts_synthesis),
        ("Backend", test_backend),
        ("Frontend", test_frontend),
        ("Ollama", test_ollama),
    ]

    for name, test_func in tests:
        print(f"\n{'-' * 60}")
        print(f"TEST: {name}")
        print(f"{'-' * 60}")
        results.append((name, test_func()))

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nPassed: {passed}/{total} ({passed * 100 // total}%)")

    if passed == total:
        print(f"\n{'=' * 60}")
        print("ALL TESTS PASSED! Ready for full E2E test.")
        print(f"{'=' * 60}")

        response = input("Run full E2E test? (takes ~5-10 minutes) [y/N]: ")
        if response.lower() in ("y", "yes"):
            asyncio.run(test_end_to_end())
    else:
        print(f"\n{'=' * 60}")
        print("Some tests failed. Fix issues above and re-run.")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
