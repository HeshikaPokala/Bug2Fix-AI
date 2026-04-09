from __future__ import annotations

from pathlib import Path

from app.orchestrator.state import WorkflowState
from app.tools.exec_tools import run_command
from app.tools.tracing import append_trace


REPRO_SCRIPT = """from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mini_repo.calculator import average

print("Running minimal repro...")
print("Input:", [])
print("Expected: 0.0 (graceful behavior)")
print("Actual:")
print(average([]))
"""


def run(state: WorkflowState) -> None:
    append_trace(state.trace_path, "agent_start", {"agent": "ReproductionAgent"})
    repro_dir = state.output_dir / "generated_repro"
    repro_dir.mkdir(parents=True, exist_ok=True)
    repro_path = repro_dir / "repro_average_empty.py"
    repro_path.write_text(REPRO_SCRIPT, encoding="utf-8")

    command = ["python3", str(repro_path)]
    result = run_command(command, cwd=state.workspace_root)

    state.repro_artifact_path = str(repro_path)
    state.repro_command = "python3 artifacts/generated_repro/repro_average_empty.py"
    state.repro_result = {
        "failed_consistently": result["return_code"] != 0,
        "return_code": result["return_code"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "failure_signature": "ZeroDivisionError" if "ZeroDivisionError" in result["stderr"] else "unknown",
    }
    append_trace(
        state.trace_path,
        "agent_end",
        {
            "agent": "ReproductionAgent",
            "artifact": state.repro_artifact_path,
            "return_code": result["return_code"],
        },
    )
