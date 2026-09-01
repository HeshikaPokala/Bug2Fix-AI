from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.agents import log_analyst
from app.orchestrator.state import WorkflowState

SAMPLE_LOG = """2026-05-02 10:01:01 INFO request_id=aa11 endpoint=/greet payload_size=1
2026-05-02 10:01:01 INFO unrelated telemetry heartbeat healthy=true
Traceback (most recent call last):
  File "service.py", line 77, in handle_greet_request
    result = format_greeting(name)
  File "mini_repo/notifier.py", line 7, in format_greeting
    return "Hello, " + name.upper() + "!"
AttributeError: 'NoneType' object has no attribute 'upper'
2026-05-02 10:01:02 ERROR request_id=aa11 status=500 endpoint=/greet
2026-05-02 10:01:03 INFO ad_service clickstream flush success
"""


class ParseFramesTests(unittest.TestCase):
    def test_parses_all_frames_in_order(self):
        frames = log_analyst._parse_frames(SAMPLE_LOG.splitlines())
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0]["file"], "service.py")
        self.assertEqual(frames[0]["function"], "handle_greet_request")
        self.assertEqual(frames[1]["file"], "mini_repo/notifier.py")
        self.assertEqual(frames[1]["function"], "format_greeting")

    def test_parses_error_type_and_message(self):
        error_type, message = log_analyst._parse_error(SAMPLE_LOG.splitlines())
        self.assertEqual(error_type, "AttributeError")
        self.assertIn("has no attribute 'upper'", message)

    def test_parses_no_error_gracefully(self):
        error_type, message = log_analyst._parse_error(["just a plain log line", "another one"])
        self.assertEqual(error_type, "unknown")
        self.assertEqual(message, "")


class ResolveExistingFrameTests(unittest.TestCase):
    def test_skips_frames_that_dont_exist_on_disk(self):
        """The traceback's first frame ('service.py') is a stand-in for a real
        production file we don't have a copy of -- the resolver must skip past
        it to the deepest frame that actually maps to a file we can act on.
        """
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            repo_root = workspace / "mini_repo"
            repo_root.mkdir()
            (repo_root / "notifier.py").write_text("def format_greeting(name):\n    return name\n")

            frames = log_analyst._parse_frames(SAMPLE_LOG.splitlines())
            resolved = log_analyst._resolve_existing_frame(frames, workspace, repo_root)

            self.assertIsNotNone(resolved)
            self.assertEqual(resolved["function"], "format_greeting")
            self.assertTrue(resolved["resolved_path"].endswith("notifier.py"))

    def test_returns_none_when_nothing_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            repo_root = workspace / "mini_repo"
            repo_root.mkdir()
            frames = log_analyst._parse_frames(SAMPLE_LOG.splitlines())
            resolved = log_analyst._resolve_existing_frame(frames, workspace, repo_root)
            self.assertIsNone(resolved)


class RunEndToEndTests(unittest.TestCase):
    def test_run_populates_likely_failure_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            repo_root = workspace / "mini_repo"
            repo_root.mkdir()
            (repo_root / "notifier.py").write_text("def format_greeting(name):\n    return name\n")
            logs_path = workspace / "app.log"
            logs_path.write_text(SAMPLE_LOG)
            trace_path = workspace / "trace.jsonl"

            state = WorkflowState(
                workspace_root=workspace,
                bug_report_path=workspace / "bug_report.md",
                logs_path=logs_path,
                repo_root=repo_root,
                output_dir=workspace / "artifacts",
                trace_path=trace_path,
                run_id="test",
            )
            log_analyst.run(state)

            self.assertEqual(state.likely_failure_surface["function"], "format_greeting")
            self.assertEqual(state.likely_failure_surface["error_type"], "AttributeError")
            self.assertTrue(trace_path.is_file())


if __name__ == "__main__":
    unittest.main()
