from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass
class WorkflowState:
    workspace_root: Path
    bug_report_path: Path
    logs_path: Path
    repo_root: Path
    output_dir: Path
    trace_path: Path
    run_id: str

    bug_summary: dict[str, Any] = field(default_factory=dict)
    triage_hypotheses: list[dict[str, Any]] = field(default_factory=list)
    log_evidence: list[dict[str, Any]] = field(default_factory=list)
    likely_failure_surface: dict[str, Any] = field(default_factory=dict)
    repro_artifact_path: str = ""
    repro_command: str = ""
    repro_result: dict[str, Any] = field(default_factory=dict)
    root_cause_hypothesis: dict[str, Any] = field(default_factory=dict)
    patch_plan: dict[str, Any] = field(default_factory=dict)
    validation_plan: dict[str, Any] = field(default_factory=dict)
    open_questions: list[str] = field(default_factory=list)
    reviewer_findings: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    final_report_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["workspace_root"] = str(self.workspace_root)
        data["bug_report_path"] = str(self.bug_report_path)
        data["logs_path"] = str(self.logs_path)
        data["repo_root"] = str(self.repo_root)
        data["output_dir"] = str(self.output_dir)
        data["trace_path"] = str(self.trace_path)
        return data
