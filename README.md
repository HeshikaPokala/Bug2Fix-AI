# Assessment 2 - Multi-Agent Bug Triage and Repro System

This project implements **Assessment 2** as a deterministic multi-agent CLI workflow.

## What it does

Given:
- a bug report
- logs
- an optional mini-repo snapshot

the system orchestrates multiple agents to:
1. triage the report,
2. extract evidence from logs,
3. generate and run a minimal reproducible script,
4. propose root cause and patch plan,
5. run a critic/reviewer pass,
6. produce a structured final JSON report.

## Agent roles

- `TriageAgent`
- `LogAnalystAgent`
- `ReproductionAgent`
- `FixPlannerAgent`
- `ReviewerCriticAgent`

Coordinator: `app/orchestrator/graph.py` (deterministic handoffs).

### Where each agent is implemented

- `app/agents/triage.py`
- `app/agents/log_analyst.py`
- `app/agents/reproduction.py`
- `app/agents/fix_planner.py`
- `app/agents/reviewer.py`

## Setup

Python 3.11+ recommended.

```bash
python3 --version
```

### CLI only (no extra packages)

The orchestrator runs with the standard library only.

### Web UI (optional)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Frontend (requires [Node.js](https://nodejs.org/) LTS):

```bash
cd frontend
npm install
npm run build
cd ..
```

## Web UI — run

Terminal 1 — API + built UI (served under `/ui` so `/docs` stays available):

```bash
source .venv/bin/activate
uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/ui/** (root `/` redirects there after a build).

- Interactive API docs: **http://127.0.0.1:8000/docs**
- Run analysis from the UI (calls `POST /api/run`) or via curl:

```bash
curl -s -X POST http://127.0.0.1:8000/api/run -H "Content-Type: application/json" -d '{}' | head -c 400
```

### Web UI — dev mode (hot reload)

Terminal 1: `uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000`  
Terminal 2:

```bash
cd frontend && npm run dev
```

Open **http://127.0.0.1:5173** — Vite proxies `/api` to port 8000.

### Web UI — Streamlit (no Node.js)

Same orchestrator, **Python only** after `pip install -r requirements.txt`:

```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

Use this if you do not want to install Node or build the React frontend.
The Streamlit app supports:
- uploading bug report (`.md`/`.json`)
- uploading logs (`.log`/`.txt`)
- optional repo snapshot upload (`.zip`)
- fallback repo path if zip is not uploaded

## Run end-to-end

```bash
python3 -m app.main --bug-report inputs/bug_report.md --logs inputs/logs/app.log --repo-root mini_repo --output-dir artifacts
```

Expected behavior:
- A minimal repro script is generated and executed.
- The repro fails with `ZeroDivisionError`.
- A final structured JSON report is produced in `artifacts/`.
- A full trace file is produced in `traces/`.

## Output artifacts

- `artifacts/generated_repro/repro_average_empty.py`
- `artifacts/Final Report.json` (overwritten on each run)
- `traces/run_<run_id>.jsonl`

## Traceability

Trace file format (`jsonl`) includes:
- `workflow_start`, `workflow_end`
- `agent_start`, `agent_end`
- tool-call-related outcomes embedded in agent payloads

Use:
```bash
python3 -m app.main ...
```
then inspect the latest file in `traces/`.

## Notes

- Secrets are not hardcoded.
- This repo is intentionally deterministic and reproducible.
- You can extend this with LLM-driven agents while preserving the same typed state contract.
