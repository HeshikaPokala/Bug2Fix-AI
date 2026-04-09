from __future__ import annotations

import re
from pathlib import Path


ERROR_PATTERN = re.compile(r"(error|exception|traceback|failed)", re.IGNORECASE)


def extract_stack_trace(log_path: Path) -> list[str]:
    lines = log_path.read_text(encoding="utf-8").splitlines()
    trace_lines: list[str] = []
    capture = False
    for line in lines:
        if "Traceback (most recent call last):" in line:
            capture = True
        if capture:
            trace_lines.append(line)
            if re.search(r"^\w*Error:", line):
                capture = False
    return trace_lines


def find_error_signatures(log_path: Path) -> list[dict[str, str]]:
    signatures: list[dict[str, str]] = []
    for line_no, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), 1):
        if ERROR_PATTERN.search(line):
            signatures.append({"line": str(line_no), "text": line.strip()})
    return signatures
