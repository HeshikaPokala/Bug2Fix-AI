from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.orchestrator.graph import run_workflow

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class EndToEndDeterministicTests(unittest.TestCase):
    """Runs the full 5-agent pipeline with use_llm=False against the checked-in
    demo bugs -- no network, no Ollama, deterministic every time. This is the
    regression net: any change that breaks the generalized diagnosis/repro/
    patch-plan logic should fail one of these.
    """

    def _run(self, bug_id_prefix: str) -> dict:
        bug_report = next((PROJECT_ROOT / "demo" / "bug_reports").glob(f"{bug_id_prefix}_*.md"))
        logs = next((PROJECT_ROOT / "demo" / "logs").glob(f"{bug_id_prefix}_*.log"))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_workflow(
                bug_report_path=bug_report,
                logs_path=logs,
                repo_root=PROJECT_ROOT / "mini_repo",
                output_dir=Path(tmp),
                workspace_root=PROJECT_ROOT,
                use_llm=False,
                traces_dir=Path(tmp) / "traces",
            )
            return json.loads(Path(result["final_report_path"]).read_text(encoding="utf-8"))

    def test_bug1_fallback_coverable_confirms_repro(self):
        report = self._run("bug1")
        self.assertEqual(report["likely_failure_surface"]["function"], "format_greeting")
        self.assertEqual(report["likely_failure_surface"]["error_type"], "AttributeError")
        self.assertTrue(report["repro"]["result"]["failed_consistently"])
        self.assertEqual(report["patch_plan"]["source"], "rule_based")

    def test_bug3_llm_required_diagnoses_correctly_but_cannot_confirm_repro(self):
        """Without LLM assistance this bug's repro genuinely can't be proven --
        the diagnosis must still be correct, and the pipeline must say so
        honestly (low confidence, high-severity reviewer finding) rather than
        silently reporting success.
        """
        report = self._run("bug3")
        self.assertEqual(report["likely_failure_surface"]["function"], "get_line_item_price")
        self.assertEqual(report["likely_failure_surface"]["error_type"], "KeyError")
        self.assertFalse(report["repro"]["result"]["failed_consistently"])
        severities = [f["severity"] for f in report["reviewer_critic_findings"]]
        self.assertIn("high", severities)
        self.assertLess(report["confidence"], 0.92)

    def test_two_different_bugs_produce_different_diagnoses(self):
        """Regression guard against the original hardcoding bug: the pipeline
        must not describe every bug as the same function/error.
        """
        report1 = self._run("bug1")
        report6 = self._run("bug6")
        self.assertNotEqual(
            report1["likely_failure_surface"]["function"], report6["likely_failure_surface"]["function"]
        )
        self.assertNotEqual(
            report1["likely_failure_surface"]["error_type"], report6["likely_failure_surface"]["error_type"]
        )

    def test_unresolvable_log_degrades_honestly(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bug_report = tmp_path / "bug_report.md"
            bug_report.write_text("Title: Something broke\n\nDescription:\nno details.\n")
            logs = tmp_path / "app.log"
            logs.write_text("2026-01-01 00:00:00 INFO everything fine\n")

            result = run_workflow(
                bug_report_path=bug_report,
                logs_path=logs,
                repo_root=PROJECT_ROOT / "mini_repo",
                output_dir=tmp_path / "artifacts",
                workspace_root=PROJECT_ROOT,
                use_llm=False,
                traces_dir=Path(tmp) / "traces",
            )
            report = json.loads(Path(result["final_report_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["likely_failure_surface"]["function"], "unknown")
            self.assertFalse(report["repro"]["result"]["failed_consistently"])
            self.assertLess(report["confidence"], 0.92)


if __name__ == "__main__":
    unittest.main()
