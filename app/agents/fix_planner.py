from __future__ import annotations

from app.orchestrator.state import WorkflowState
from app.tools.repo_tools import repo_search
from app.tools.tracing import append_trace


def run(state: WorkflowState) -> None:
    append_trace(state.trace_path, "agent_start", {"agent": "FixPlannerAgent"})
    matches = repo_search(state.repo_root, r"def average")
    failure_signature = state.repro_result.get("failure_signature", "unknown")
    stack_excerpt = []
    for block in state.log_evidence:
        if block.get("type") == "stack_trace":
            stack_excerpt = block.get("lines", [])[:3]
            break

    state.root_cause_hypothesis = {
        "statement": "Failure is likely caused by missing empty-input guard in arithmetic path (average), causing runtime error.",
        "confidence": 0.9 if failure_signature != "unknown" else 0.72,
        "supporting_evidence": [
            f"Reproduction result signature: {failure_signature}",
            "Repository search found average() implementation",
            f"Stack trace excerpt: {' | '.join(stack_excerpt) if stack_excerpt else 'n/a'}",
        ],
    }
    state.patch_plan = {
        "files_impacted": ["mini_repo/calculator.py", "mini_repo/tests/test_calculator.py"],
        "approach": [
            "Add guard clause in average(nums): return 0.0 when nums is empty.",
            "Add unit tests for empty, single-value, and mixed-value lists.",
            "Add input validation for None to avoid TypeError.",
        ],
        "risks": [
            "Silent default on empty input may hide upstream data issues.",
            "Behavioral change could affect callers expecting exception semantics.",
        ],
        "repo_search_hits": matches[:5],
    }
    state.validation_plan = {
        "tests_to_add": [
            "test_average_empty_returns_zero",
            "test_average_singleton",
            "test_average_regular_values",
        ],
        "regression_checks": [
            "Run full test suite",
            "Replay recent batch payloads",
            f"Check error-rate dashboard for drop in {failure_signature}",
        ],
    }
    append_trace(
        state.trace_path,
        "agent_end",
        {"agent": "FixPlannerAgent", "repo_hits": len(matches)},
    )
