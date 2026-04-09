from __future__ import annotations

import argparse
from pathlib import Path

from app.orchestrator.graph import run_workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assessment 2 multi-agent bug triage orchestrator"
    )
    parser.add_argument(
        "--bug-report",
        default="inputs/bug_report.md",
        help="Path to bug report markdown/json file",
    )
    parser.add_argument(
        "--logs",
        default="inputs/logs/app.log",
        help="Path to application logs file",
    )
    parser.add_argument(
        "--repo-root",
        default="mini_repo",
        help="Path to repository snapshot used for investigation",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts",
        help="Directory where final outputs are written",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_workflow(
        bug_report_path=Path(args.bug_report),
        logs_path=Path(args.logs),
        repo_root=Path(args.repo_root),
        output_dir=output_dir,
    )
    print(f"Decision complete. Report: {result['final_report_path']}")
    print(f"Trace file: {result['trace_path']}")
    print(f"Reproduction artifact: {result['repro_artifact_path']}")


if __name__ == "__main__":
    main()
