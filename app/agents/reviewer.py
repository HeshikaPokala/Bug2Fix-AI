from __future__ import annotations

from app.orchestrator.state import WorkflowState
from app.tools.tracing import append_trace


def run(state: WorkflowState) -> None:
    append_trace(state.trace_path, "agent_start", {"agent": "ReviewerCriticAgent"})
    findings = []
    expected_error = state.likely_failure_surface.get("error_type", "unknown")

    if not state.repro_result.get("failed_consistently", False):
        findings.append(
            {
                "severity": "high",
                "issue": "Reproduction did not fail consistently (or could not be synthesized). Root cause confidence should be downgraded.",
            }
        )
    if expected_error != "unknown" and expected_error not in state.repro_result.get("stderr", ""):
        findings.append(
            {
                "severity": "medium",
                "issue": f"Failure signature mismatch: logs indicate {expected_error}, but reproduction stderr does not contain it.",
            }
        )

    findings.append(
        {
            "severity": "low",
            "issue": "Add explicit decision note on whether the triggering input should be treated as valid domain input.",
        }
    )
    state.reviewer_findings = findings
    state.open_questions = [
        f"Should the input that triggers {expected_error} be treated as valid, or rejected earlier in the pipeline?",
        "Is there any caller that depends on the previous (crashing) behavior?",
    ]
    state.confidence = 0.92 if len(findings) == 1 else 0.74
    append_trace(
        state.trace_path,
        "agent_end",
        {"agent": "ReviewerCriticAgent", "findings": len(findings), "confidence": state.confidence},
    )
