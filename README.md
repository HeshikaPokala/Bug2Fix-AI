# Bug Triage, Reproduction, and Fix Planning System

This project is a lightweight Python system that takes a bug report, logs, and optionally a small repository, and runs them through a structured pipeline to diagnose and plan fixes.

The system:
- Parses and understands the bug report  
- Extracts meaningful signals from logs  
- Generates and executes a minimal reproduction  
- Produces a root-cause hypothesis, patch plan, and validation steps  

Outputs are written to:
- `artifacts/Final Report.json`  
- `traces/` (per-run execution logs)

> The pipeline is fully deterministic and rule-based by default — no API keys or LLM dependency required.

---

## Orchestration

The coordinator (`app/orchestrator/graph.py`) runs a **linear, explicit workflow**:

```
Triage → Log Analyst → Reproduction → Fix Planner → Reviewer
```

- Each step updates a shared `WorkflowState` (`state.py`)  
- One JSONL trace file is created per run under `traces/`  
- Execution is simple, readable, and easy to debug  

> No graph frameworks (e.g., LangGraph) are used — the design favors clarity over abstraction.

---

## Agents

Each agent lives in `app/agents/` and operates on the same shared state.

### Triage
- Parses bug report fields (title, expected vs actual, environment)  
- Assigns severity heuristically  
- Outputs initial hypotheses  

---

### Log Analyst
- Scans logs for error patterns and tracebacks  
- Extracts relevant failure signals  
- Includes some noise to reflect real-world logs  

---

### Reproduction
- Generates a minimal repro script (`artifacts/generated_repro/`)  
- Executes it using subprocess  
- Captures stdout, stderr, exit code, and failure signature  

---

### Fix Planner
- Searches the repo (via ripgrep or fallback)  
- Produces:
  - Root cause hypothesis  
  - Patch plan  
  - Validation plan  

---

### Reviewer / Critic
- Verifies consistency between logs and repro results  
- Flags mismatches or weak assumptions  
- Outputs a final confidence score  

---

## Tools

Located in `app/tools/`:

- **log_tools.py** — log parsing and traceback extraction  
- **exec_tools.py** — subprocess execution helpers  
- **repo_tools.py** — repo search (rg or fallback)  
- **tracing.py** — structured JSONL logging  

> Tools are directly invoked in code — no simulated tool-calling via prompts.

---

## Sample Bug

Included in `inputs/`:

- Bug report (markdown)  
- Application logs (with real traceback + noise)  
- `mini_repo/` — toy codebase where `average([])` triggers a `ZeroDivisionError`  

The system generates a repro script that intentionally fails to validate the pipeline.

---

## Outputs

- `artifacts/Final Report.json` — overwritten each run  
- `artifacts/generated_repro/` — repro scripts  
- `traces/run_<UTC>.jsonl` — execution trace per run  

The final report includes:
- Root cause hypothesis  
- Patch plan  
- Validation steps  
- Confidence signals (planner vs reviewer)  
- Repro execution details (exit code, failure signature)  

---

## Project Structure

```
app/
  agents/
  orchestrator/
  tools/
  api/
frontend/
inputs/
mini_repo/
artifacts/
traces/
```

---

## Setup

Core pipeline (no extra dependencies):

```
python3 -m app.main \
  --bug-report inputs/bug_report.md \
  --logs inputs/logs/app.log \
  --repo-root mini_repo \
  --output-dir artifacts
```

---

### Optional Setup (UI / API)

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running the UI

### Streamlit

```
streamlit run streamlit_app.py
```

- Upload bug report and logs  
- Optionally provide repo (or use `mini_repo`)  

---

### FastAPI + React UI

```
cd frontend
npm install
npm run build
cd ..

uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000
```

- UI: http://127.0.0.1:8000/ui/  
- API Docs: http://127.0.0.1:8000/docs  

For development:
- Run `uvicorn` (backend)  
- Run `npm run dev` (frontend with hot reload)  

---

## Key Idea

This system is designed to mirror how engineers debug issues in practice:

- Start with incomplete information  
- Extract signal from noisy logs  
- Validate assumptions via reproduction  
- Propose fixes grounded in evidence  

It prioritizes **clarity, traceability, and determinism** over abstraction.
