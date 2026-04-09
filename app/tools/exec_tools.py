from __future__ import annotations

import subprocess
from pathlib import Path


def run_command(command: list[str], cwd: Path | None = None) -> dict[str, str | int]:
    proc = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "return_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
