from __future__ import annotations

from pathlib import Path
import re

from app.orchestrator.state import WorkflowState
from app.tools.log_tools import extract_stack_trace, find_error_signatures
from app.tools.tracing import append_trace

_FRAME_PATTERN = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<func>\S+)')
_ERROR_LINE_PATTERN = re.compile(r"^(?P<error_type>\w+(?:Error|Exception)):\s*(?P<message>.*)$")


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


def _parse_frames(stack: list[str]) -> list[dict[str, str]]:
    frames: list[dict[str, str]] = []
    for line in stack:
        match = _FRAME_PATTERN.search(line)
        if match:
            frames.append(
                {"file": match.group("file"), "line": match.group("line"), "function": match.group("func")}
            )
    return frames


def _parse_error(stack: list[str]) -> tuple[str, str]:
    for line in reversed(stack):
        match = _ERROR_LINE_PATTERN.match(line.strip())
        if match:
            return match.group("error_type"), match.group("message")
    return "unknown", ""


def _resolve_existing_frame(
    frames: list[dict[str, str]], workspace_root: Path, repo_root: Path
) -> dict[str, str] | None:
    """Walk the traceback deepest-first and return the first frame that maps to a
    real file we have access to. Logs often reference files outside the provided
    repo snapshot (e.g. a service entrypoint) -- those frames can't be reproduced,
    so we skip past them to the deepest frame we can actually act on.
    """
    for frame in reversed(frames):
        candidate = Path(frame["file"])
        for base in (workspace_root, repo_root, repo_root.parent):
            resolved = candidate if candidate.is_absolute() else (base / candidate)
            if resolved.is_file():
                return {**frame, "resolved_path": str(resolved.resolve())}
    return None


def run(state: WorkflowState) -> None:
    append_trace(state.trace_path, "agent_start", {"agent": "LogAnalystAgent"})
    signatures = find_error_signatures(state.logs_path)
    stack = extract_stack_trace(state.logs_path)
    versions = _version_correlations(state.logs_path)
    noise = _noise_lines(state.logs_path)

    frames = _parse_frames(stack)
    error_type, error_message = _parse_error(stack)
    resolved = _resolve_existing_frame(frames, state.workspace_root, state.repo_root)

    state.log_evidence = [
        {"type": "error_signatures", "count": len(signatures), "items": signatures[:8]},
        {"type": "stack_trace", "lines": stack[:16]},
        {"type": "correlated_versions", "items": [{"line": "-", "text": v} for v in versions]},
        {"type": "noise_red_herrings", "count": len(noise), "items": [{"line": "-", "text": n} for n in noise]},
    ]

    if resolved:
        state.likely_failure_surface = {
            "module": resolved["file"],
            "resolved_path": resolved["resolved_path"],
            "function": resolved["function"],
            "error_type": error_type,
            "error_message": error_message,
            "reason": (
                f"Deepest resolvable stack frame points to {resolved['function']}() in "
                f"{resolved['file']} (line {resolved['line']}), raising "
                f"{error_type if error_type != 'unknown' else 'an unrecognized exception'}."
            ),
        }
    else:
        state.likely_failure_surface = {
            "module": "unknown",
            "resolved_path": "",
            "function": "unknown",
            "error_type": error_type,
            "error_message": error_message,
            "reason": "No stack frame in the logs resolved to a file inside the provided repository.",
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
            "resolved_function": state.likely_failure_surface["function"],
            "error_type": error_type,
        },
    )
