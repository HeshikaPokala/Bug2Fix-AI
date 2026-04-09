from __future__ import annotations

from app.orchestrator.state import WorkflowState
from app.tools.tracing import append_trace


def run(state: WorkflowState) -> None:
    append_trace(state.trace_path, "agent_start", {"agent": "ReviewerCriticAgent"})
    findings = []
    if not state.repro_result.get("failed_consistently", False):
        findings.append(
            {
                "severity": "high",
                "issue": "Reproduction did not fail consistently. Root cause confidence should be downgraded.",
            }
        )
    if "ZeroDivisionError" not in state.repro_result.get("stderr", ""):
        findings.append(
            {
                "severity": "medium",
                "issue": "Failure signature mismatch between logs and repro.",
            }
        )

    findings.append(
        {
            "severity": "low",
            "issue": "Add explicit decision note on whether empty list should be valid domain input.",
        }
    )
    state.reviewer_findings = findings
    state.open_questions = [
        "Should empty input return 0.0 or raise a domain-specific exception?",
        "Is there any caller that depends on previous crashing behavior?",
    ]
    state.confidence = 0.92 if len(findings) == 1 else 0.74
    append_trace(
        state.trace_path,
        "agent_end",
        {"agent": "ReviewerCriticAgent", "findings": len(findings), "confidence": state.confidence},
    )
