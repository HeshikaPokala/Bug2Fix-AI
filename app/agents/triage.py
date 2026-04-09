from __future__ import annotations

from pathlib import Path
import re

from app.orchestrator.state import WorkflowState
from app.tools.tracing import append_trace


def _extract_field(text: str, field: str) -> str:
    pattern = re.compile(rf"^{re.escape(field)}\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def run(state: WorkflowState) -> None:
    append_trace(state.trace_path, "agent_start", {"agent": "TriageAgent"})
    text = Path(state.bug_report_path).read_text(encoding="utf-8")

    title = _extract_field(text, "Title") or "Unknown bug"
    expected = _extract_field(text, "Expected behavior") or "Not specified"
    actual = _extract_field(text, "Actual behavior") or "Not specified"
    environment = _extract_field(text, "Environment") or "Not specified"
    description = _extract_field(text, "Description") or "No description provided"

    severity = "high" if ("500" in text or "crash" in text.lower() or "exception" in text.lower()) else "medium"
    likely_scope = "Single endpoint failure surface (based on report hints)"

    state.bug_summary = {
        "title": title,
        "symptoms": description,
        "severity": severity,
        "scope": likely_scope,
        "expected_behavior": expected,
        "actual_behavior": actual,
        "environment": environment,
    }
    state.triage_hypotheses = [
        {
            "id": "H1",
            "hypothesis": "A math/path edge case causes runtime exception on empty input.",
            "priority": 1,
        },
        {
            "id": "H2",
            "hypothesis": "Input validation is missing and malformed/empty payload reaches core logic.",
            "priority": 2,
        },
        {
            "id": "H3",
            "hypothesis": "Recent deployment changed handling semantics for empty collections.",
            "priority": 3,
        },
    ]
    append_trace(
        state.trace_path,
        "agent_end",
        {
            "agent": "TriageAgent",
            "title": state.bug_summary["title"],
            "severity": severity,
            "hypothesis_count": len(state.triage_hypotheses),
        },
    )
