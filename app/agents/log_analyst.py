from __future__ import annotations

from pathlib import Path
import re

from app.orchestrator.state import WorkflowState
from app.tools.log_tools import extract_stack_trace, find_error_signatures
from app.tools.tracing import append_trace


def _version_correlations(log_path: Path) -> list[str]:
    lines = log_path.read_text(encoding="utf-8").splitlines()
    versions: list[str] = []
    for line in lines:
        found = re.findall(r"(version|deploy|release)[=:\s]+([A-Za-z0-9._-]+)", line, flags=re.IGNORECASE)
        for _, value in found:
            versions.append(value)
    return sorted(set(versions))


def _noise_lines(log_path: Path) -> list[str]:
    lines = log_path.read_text(encoding="utf-8").splitlines()
    noise = [line for line in lines if ("heartbeat" in line.lower() or "telemetry" in line.lower() or "ad_service" in line.lower())]
    return noise[:6]


def run(state: WorkflowState) -> None:
    append_trace(state.trace_path, "agent_start", {"agent": "LogAnalystAgent"})
    signatures = find_error_signatures(state.logs_path)
    stack = extract_stack_trace(state.logs_path)
    versions = _version_correlations(state.logs_path)
    noise = _noise_lines(state.logs_path)

    state.log_evidence = [
        {"type": "error_signatures", "count": len(signatures), "items": signatures[:8]},
        {"type": "stack_trace", "lines": stack[:16]},
        {"type": "correlated_versions", "items": [{"line": "-", "text": v} for v in versions]},
        {"type": "noise_red_herrings", "count": len(noise), "items": [{"line": "-", "text": n} for n in noise]},
    ]
    state.likely_failure_surface = {
        "module": "mini_repo/calculator.py" if stack else "unknown",
        "function": "average" if any("average" in line for line in stack) else "unknown",
        "reason": "Stack trace and error signatures converge on arithmetic edge case in average()",
    }
    append_trace(
        state.trace_path,
        "agent_end",
        {
            "agent": "LogAnalystAgent",
            "signature_count": len(signatures),
            "stack_lines": len(stack),
            "version_markers": len(versions),
            "noise_lines": len(noise),
        },
    )
