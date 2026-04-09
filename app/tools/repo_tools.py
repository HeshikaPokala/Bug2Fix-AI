from __future__ import annotations

import subprocess
import re
from pathlib import Path


def repo_search(repo_root: Path, pattern: str) -> list[str]:
    cmd = ["rg", "-n", pattern, str(repo_root)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        fallback: list[str] = []
        needle = re.compile(pattern)
        for file_path in repo_root.rglob("*.py"):
            for line_no, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
                if needle.search(line):
                    fallback.append(f"{file_path}:{line_no}:{line.strip()}")
        return fallback
    if proc.returncode not in (0, 1):
        return [f"rg_failed: {proc.stderr.strip()}"]
    output = [line for line in proc.stdout.splitlines() if line.strip()]
    return output
