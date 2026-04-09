# Bug Triage, Reproduction, and Fix Planning System

This is a small Python system where you feed a bug report, logs, and optionally a tiny repo. It runs a fixed pipeline of agents that parse inputs, extract evidence from logs, generate and execute a minimal repro script, then produce a root-cause hypothesis, patch plan, and validation steps. Results are written to artifacts/Final Report.json with per-run traces under traces/.

There is no LLM in the default path. It is rule-based by default, so runs are deterministic and require no API keys.

## What the orchestration actually is

The coordinator is app/orchestrator/graph.py. The function run_workflow(...) resolves paths against a workspace_root (project root when you use Streamlit or the API, otherwise your cwd), creates one JSONL file per run under traces/, builds a WorkflowState from app/orchestrator/state.py, then calls five modules in order:

Triage → Log analyst → Reproduction → Fix planner → Reviewer/critic

Each step is just some_agent.run(state) mutating the same dataclass. That’s the whole graph: linear, explicit, and easy to read in one file.

We did not use LangGraph (it isn’t in requirements.txt and nothing imports it). If you wanted branching or LLM nodes later, you could hang the same run(state) functions off a real graph library; the state object and trace format would carry over fine.

## The five agents

Code lives in app/agents/. Each one writes agent_start / agent_end lines into the trace via app/tools/tracing.py.

**Triage** (triage.py) — Reads the bug report markdown, pulls out title / expected / actual / environment style fields with simple patterns, sets severity heuristically, fills bug_summary and triage_hypotheses.

**Log analyst** (log_analyst.py) — Scans inputs-style logs for error-ish lines, tries to grab a Python traceback block, collects a few “noise” lines so it’s obvious the pipeline isn’t only matching the happy stack trace. Output lands in log_evidence and likely_failure_surface.

**Reproduction** (reproduction.py) — Drops a script under artifacts/generated_repro/, runs it with subprocess from workspace_root, stores stdout/stderr, return code, and a rough failure_signature string (e.g. ZeroDivisionError when it shows up in stderr).

**Fix planner** (fix_planner.py) — Searches the repo with ripgrep if installed, otherwise walks .py files. Fills root_cause_hypothesis, patch_plan, validation_plan, wired to what the repro actually did and what showed up in logs.

**Reviewer** (reviewer.py) — Sanity checks: did the repro fail? Does stderr smell like the same error family as the story in the logs? Appends critic findings and sets a single confidence float on the state. open_questions still exists in the JSON export; the Streamlit UI doesn’t show that block anymore by choice.

## Tools

app/tools/log_tools.py — grep-style log helpers and traceback extraction.

app/tools/exec_tools.py — subprocess wrapper for the repro.

app/tools/repo_tools.py — repo search (rg with regex, or a dumb Python fallback if rg isn’t on PATH).

app/tools/tracing.py — one JSON object per line for the run log.

Agents import these directly; nothing is “prompted” to pretend it called a tool.

## The sample bug

Under inputs/ there’s a markdown report and app.log with a real traceback plus some junk lines. mini_repo/ is a toy module where average([]) blows up with ZeroDivisionError. The generated repro script calls that path so your run fails loudly on purpose.

## Outputs

- artifacts/Final Report.json — overwritten each run (stable name for demos).
- artifacts/generated_repro/repro_average_empty.py — regenerated; run from repo root with python3 artifacts/generated_repro/repro_average_empty.py if you want to see the failure without the full pipeline.
- traces/run_<UTC>.jsonl — one file per invocation; that’s what you point to for “traceability.”

The JSON still has two different “confidence” ideas: the fix planner’s hypothesis confidence and the reviewer’s final scalar after the critic pass. Exit code and failure_signature on the repro are there so you can see whether the run matches the log narrative.

## Layout

    app/main.py
    app/orchestrator/
    app/agents/
    app/tools/
    app/api/server.py
    streamlit_app.py
    frontend/
    inputs/
    mini_repo/

## Setup

Python 3.11+ is a good target.

Core pipeline only needs the stdlib:

    python3 -m app.main --bug-report inputs/bug_report.md --logs inputs/logs/app.log --repo-root mini_repo --output-dir artifacts

You should get a non-zero repro, an updated Final Report.json, and a new line in traces/.

For Streamlit or the HTTP API:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

(On Windows, use .venv\Scripts\activate instead of source.)

## Running the UIs

Streamlit (no Node; upload report + logs, optional zip or fallback path mini_repo):

    streamlit run streamlit_app.py

FastAPI + static React build (needs Node once to build):

    cd frontend && npm install && npm run build && cd ..
    uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000

UI at http://127.0.0.1:8000/ui/ when the build exists; Swagger at /docs. For local dev with hot reload on the frontend, run uvicorn in one terminal and npm run dev in frontend/ in another (Vite proxies /api).
