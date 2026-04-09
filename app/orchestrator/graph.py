from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.agents import fix_planner, log_analyst, reproduction, reviewer, triage
from app.orchestrator.state import WorkflowState
from app.tools.tracing import append_trace

FINAL_REPORT_FILENAME = "Final Report.json"


def _run_id() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _resolve(path: Path, base: Path) -> Path:
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def run_workflow(
    bug_report_path: Path,
    logs_path: Path,
    repo_root: Path,
    output_dir: Path,
    workspace_root: Path | None = None,
) -> dict[str, str]:
    base = (workspace_root or Path.cwd()).resolve()
    bug = _resolve(bug_report_path, base)
    logs = _resolve(logs_path, base)
    repo = _resolve(repo_root, base)
    out = _resolve(output_dir, base)
    traces_dir = base / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    run_id = _run_id()
    trace_path = traces_dir / f"run_{run_id}.jsonl"

    state = WorkflowState(
        workspace_root=base,
        bug_report_path=bug,
        logs_path=logs,
        repo_root=repo,
        output_dir=out,
        trace_path=trace_path,
        run_id=run_id,
    )
    append_trace(trace_path, "workflow_start", {"run_id": run_id})

    triage.run(state)
    log_analyst.run(state)
    reproduction.run(state)
    fix_planner.run(state)
    reviewer.run(state)

    final = {
        "bug_summary": state.bug_summary,
        "triage_hypotheses": state.triage_hypotheses,
        "likely_failure_surface": state.likely_failure_surface,
        "evidence": state.log_evidence,
        "repro": {
            "steps": ["Run generated repro script", "Observe ZeroDivisionError on empty list input"],
            "artifact_path": state.repro_artifact_path,
            "command": state.repro_command,
            "result": state.repro_result,
        },
        "root_cause_hypothesis": state.root_cause_hypothesis,
        "patch_plan": state.patch_plan,
        "validation_plan": state.validation_plan,
        "reviewer_critic_findings": state.reviewer_findings,
        "open_questions": state.open_questions,
        "confidence": state.confidence,
    }
    report_path = out / FINAL_REPORT_FILENAME
    report_path.write_text(json.dumps(final, indent=2, ensure_ascii=True), encoding="utf-8")
    state.final_report_path = str(report_path)

    append_trace(
        trace_path,
        "workflow_end",
        {"run_id": run_id, "final_report_path": str(report_path)},
    )
    return {
        "final_report_path": str(report_path),
        "trace_path": str(trace_path),
        "repro_artifact_path": state.repro_artifact_path,
    }
