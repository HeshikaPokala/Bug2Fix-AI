from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.orchestrator.graph import run_workflow

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

SAFE_REPORT = re.compile(r"^Final Report\.json$")
SAFE_TRACE = re.compile(r"^run_[0-9TZ]+\.jsonl$")


class RunRequest(BaseModel):
    bug_report: str = Field(default="inputs/bug_report.md")
    logs: str = Field(default="inputs/logs/app.log")
    repo_root: str = Field(default="mini_repo")
    output_dir: str = Field(default="artifacts")


def _read_trace_jsonl(path: Path) -> list[dict]:
    events: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def create_app() -> FastAPI:
    app = FastAPI(title="Bug Triage War Room", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:4173",
            "http://localhost:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/run")
    async def run_analysis(body: RunRequest) -> JSONResponse:
        def _execute() -> dict:
            result = run_workflow(
                bug_report_path=Path(body.bug_report),
                logs_path=Path(body.logs),
                repo_root=Path(body.repo_root),
                output_dir=Path(body.output_dir),
                workspace_root=PROJECT_ROOT,
            )
            report_path = Path(result["final_report_path"])
            trace_path = Path(result["trace_path"])
            report_obj = json.loads(report_path.read_text(encoding="utf-8"))
            trace_events = _read_trace_jsonl(trace_path)
            return {
                "paths": result,
                "report": report_obj,
                "trace": trace_events,
            }

        try:
            payload = await asyncio.to_thread(_execute)
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        return JSONResponse(content=payload)

    @app.get("/api/report/{filename}")
    async def get_report(filename: str) -> JSONResponse:
        if not SAFE_REPORT.match(filename):
            raise HTTPException(status_code=400, detail="Invalid report filename")
        path = PROJECT_ROOT / "artifacts" / filename
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Report not found")
        data = json.loads(path.read_text(encoding="utf-8"))
        return JSONResponse(content=data)

    @app.get("/api/trace/{filename}")
    async def get_trace(filename: str) -> JSONResponse:
        if not SAFE_TRACE.match(filename):
            raise HTTPException(status_code=400, detail="Invalid trace filename")
        path = PROJECT_ROOT / "traces" / filename
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Trace not found")
        return JSONResponse(content=_read_trace_jsonl(path))

    index_html = FRONTEND_DIST / "index.html"
    if FRONTEND_DIST.is_dir() and index_html.is_file():
        app.mount(
            "/ui",
            StaticFiles(directory=str(FRONTEND_DIST), html=True),
            name="frontend",
        )

        @app.get("/")
        async def root_redirect() -> RedirectResponse:
            return RedirectResponse(url="/ui/", status_code=307)
    else:

        @app.get("/")
        async def root_info() -> dict[str, str]:
            return {
                "message": "Bug triage API",
                "docs": "/docs",
                "ui_hint": "cd frontend && npm install && npm run build, then open /ui/",
            }

    return app


app = create_app()
