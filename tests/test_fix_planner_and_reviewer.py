from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.agents import fix_planner, reviewer
from app.orchestrator.state import WorkflowState


def _make_state(**overrides) -> WorkflowState:
    # Deliberately not a context manager: the returned state's workspace_root must
    # stay alive for the duration of the test (fix_planner shells out to `rg`
    # against repo_root), so the dir is left for the OS to clean up on its own
    # rather than being deleted the moment this helper returns.
    workspace = Path(tempfile.mkdtemp(prefix="bug2fix_test_"))
    (workspace / "mini_repo").mkdir(parents=True, exist_ok=True)
    defaults = dict(
        workspace_root=workspace,
        bug_report_path=workspace / "bug_report.md",
        logs_path=workspace / "app.log",
        repo_root=workspace / "mini_repo",
        output_dir=workspace / "artifacts",
        trace_path=workspace / "trace.jsonl",
        run_id="test",
        use_llm=False,
    )
    defaults.update(overrides)
    return WorkflowState(**defaults)


class FixPlannerTemplateTests(unittest.TestCase):
    def test_known_error_type_uses_specific_template(self):
        state = _make_state(
            likely_failure_surface={
                "function": "average",
                "module": "mini_repo/calculator.py",
                "resolved_path": "",
                "error_type": "ZeroDivisionError",
            },
            log_evidence=[],
            repro_result={"failed_consistently": True, "failure_signature": "ZeroDivisionError"},
        )
        fix_planner.run(state)
        self.assertIn("guard clause", state.patch_plan["approach"][0].lower())
        self.assertEqual(state.patch_plan["source"], "rule_based")

    def test_unrecognized_error_type_falls_back_to_default_template(self):
        state = _make_state(
            likely_failure_surface={
                "function": "withdraw",
                "module": "mini_repo/wallet.py",
                "resolved_path": "",
                "error_type": "InsufficientFundsError",
            },
            log_evidence=[],
            repro_result={"failed_consistently": True, "failure_signature": "InsufficientFundsError"},
        )
        fix_planner.run(state)
        self.assertIn("input validation", state.patch_plan["approach"][0].lower())

    def test_unresolved_function_gives_low_confidence(self):
        state = _make_state(
            likely_failure_surface={"function": "unknown", "module": "unknown", "resolved_path": "", "error_type": "unknown"},
            log_evidence=[],
            repro_result={"failed_consistently": False, "failure_signature": "unknown"},
        )
        fix_planner.run(state)
        self.assertLess(state.root_cause_hypothesis["confidence"], 0.5)
        self.assertEqual(state.patch_plan["files_impacted"], [])


class ReviewerTests(unittest.TestCase):
    def test_confirmed_repro_matching_error_gives_high_confidence(self):
        state = _make_state(
            likely_failure_surface={"error_type": "ZeroDivisionError"},
            repro_result={"failed_consistently": True, "stderr": "ZeroDivisionError: division by zero"},
        )
        reviewer.run(state)
        self.assertEqual(state.confidence, 0.92)
        self.assertEqual(len(state.reviewer_findings), 1)

    def test_unconfirmed_repro_flags_high_severity_and_lowers_confidence(self):
        state = _make_state(
            likely_failure_surface={"error_type": "KeyError"},
            repro_result={"failed_consistently": False, "stderr": ""},
        )
        reviewer.run(state)
        self.assertEqual(state.confidence, 0.74)
        severities = [f["severity"] for f in state.reviewer_findings]
        self.assertIn("high", severities)

    def test_mismatched_error_signature_flagged_medium(self):
        state = _make_state(
            likely_failure_surface={"error_type": "KeyError"},
            repro_result={"failed_consistently": True, "stderr": "TypeError: something else"},
        )
        reviewer.run(state)
        severities = [f["severity"] for f in state.reviewer_findings]
        self.assertIn("medium", severities)


if __name__ == "__main__":
    unittest.main()
