"""Generates mini_repo/<module>.py, demo/bug_reports/, and demo/logs/ for every
bug in bug_catalog.py. Only touches files for the ids listed in the catalog
(bugs 1-9 are hand-written and untouched by this script) -- re-run any time the
catalog changes, it's idempotent.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bug_catalog import BUGS  # noqa: E402

BUG_REPORT_TEMPLATE = """Title: {title}

Description:
{description}

Expected behavior:
{expected}

Actual behavior:
{actual}

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- {hint}
"""

LOG_TEMPLATE = """{ts0} INFO request_id={rid} endpoint={endpoint} payload_size=1
{ts0} WARN request_id={rid} unusual payload received: {warn_detail}
{ts0} DEBUG request_id={rid} entering {function}
{ts0} INFO unrelated telemetry heartbeat healthy=true
Traceback (most recent call last):
  File "service.py", line {caller_line}, in {caller_func}
    result = {function}(...)
  File "mini_repo/{module}.py", line {crash_line}, in {function}
    {crash_statement}
{error_type}: {error_message}
{ts1} ERROR request_id={rid} status=500 endpoint={endpoint}
{ts2} INFO ad_service clickstream flush success
"""


def _find_crash_line(source: str, crash_statement: str) -> int:
    for i, line in enumerate(source.splitlines(), start=1):
        if line.strip() == crash_statement.strip():
            return i
    raise ValueError(f"crash_statement {crash_statement!r} not found verbatim in source")


def main() -> None:
    mini_repo = PROJECT_ROOT / "mini_repo"
    bug_reports_dir = PROJECT_ROOT / "demo" / "bug_reports"
    logs_dir = PROJECT_ROOT / "demo" / "logs"
    mini_repo.mkdir(parents=True, exist_ok=True)
    bug_reports_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    base_date = datetime(2026, 5, 11)

    for i, bug in enumerate(BUGS):
        module_path = mini_repo / f"{bug['module']}.py"
        module_path.write_text("from __future__ import annotations\n\n\n" + bug["source"], encoding="utf-8")

        crash_line = _find_crash_line(module_path.read_text(encoding="utf-8"), bug["crash_statement"])

        report_path = bug_reports_dir / f"bug{bug['id']}_{bug['slug']}.md"
        report_path.write_text(
            BUG_REPORT_TEMPLATE.format(
                title=bug["title"], description=bug["description"], expected=bug["expected"], actual=bug["actual"], hint=bug["hint"]
            ),
            encoding="utf-8",
        )

        day = base_date + timedelta(days=i)
        ts0 = day.strftime("%Y-%m-%d %H:%M:01")
        ts1 = day.strftime("%Y-%m-%d %H:%M:02")
        ts2 = day.strftime("%Y-%m-%d %H:%M:03")
        rid = f"g{bug['id']:03d}"
        log_path = logs_dir / f"bug{bug['id']}_{bug['slug']}.log"
        log_path.write_text(
            LOG_TEMPLATE.format(
                ts0=ts0,
                ts1=ts1,
                ts2=ts2,
                rid=rid,
                endpoint=bug["endpoint"],
                warn_detail=bug["warn_detail"],
                function=bug["function"],
                caller_line=50 + i * 3,
                caller_func=bug["caller_func"],
                module=bug["module"],
                crash_line=crash_line,
                crash_statement=bug["crash_statement"],
                error_type=bug["error_type"],
                error_message=bug["error_message"],
            ),
            encoding="utf-8",
        )
        print(f"bug{bug['id']} ({bug['category']}): {module_path.name}, {report_path.name}, {log_path.name}")

    print(f"\nGenerated {len(BUGS)} bugs (ids {BUGS[0]['id']}-{BUGS[-1]['id']}).")


if __name__ == "__main__":
    main()
