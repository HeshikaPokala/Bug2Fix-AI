from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.orchestrator.state import utc_now


def append_trace(trace_path: Path, event_type: str, payload: dict[str, Any]) -> None:
    record = {"ts": utc_now(), "event": event_type, "payload": payload}
    with trace_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True) + "\n")
