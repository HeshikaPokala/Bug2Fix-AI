# Assessment 2 — Multi-Agent Bug Triage, Reproduction, and Fix Planning

This repository implements **Multi-agent system** that ingests a **bug report**, **logs**, and an optional **repository snapshot**, then produces a **minimal reproduction**, a **root-cause hypothesis**, a **patch plan**, **verification steps**, and a **structured final report** — with full **traceability** of agent steps and tool usage.

---

## Objective (what the assessment asked for)

The goal is to simulate an **automated engineering assistant** that can:

1. **Parse inputs** — bug report + logs + optional repo snapshot.  
2. **Triage** — identify the most likely failure surface.  
3. **Extract evidence** from logs (stack traces, error signatures, noise vs signal).  
4. **Generate and run** a **minimal reproducible** script or test (real execution, not only text).  
5. **Summarize** observed behavior and **align** it with log evidence.  
6. **Propose** a credible **root cause**, **patch plan**, and **validation / regression** strategy.  
7. **Expose orchestration** — clear agent roles, a **coordinator**, **explicit handoffs**, and **logs or traces** of decisions and **programmatic tool calls**.

This solution is **deterministic and reproducible** (no API keys required for the default path), which makes it easy to **demo**, **grade**, and **extend** with LLMs later.

---

## What we built (summary)

| Layer | What it is |
|--------|------------|
| **Orchestrator** | A **linear state-machine-style workflow** in Python (`app/orchestrator/graph.py`) that owns execution order and builds the final report. |
| **Shared state** | A typed **`WorkflowState`** dataclass (`app/orchestrator/state.py`) passed sequentially through every agent. |
| **Agents** | Five modules under `app/agents/`, each with a single `run(state)` entrypoint. |
| **Tools** | Plain Python functions under `app/tools/` (log parsing, subprocess execution, repo search, JSONL tracing). Agents call these **programmatically**. |
| **Sample scenario** | A **mini-repo** with an intentional bug (`mini_repo/`), plus sample **bug report** and **logs** under `inputs/`. |
| **Outputs** | **`artifacts/Final Report.json`**, a **generated repro script**, and **`traces/run_<UTC>.jsonl`** per run. |
| **UIs (optional)** | **Streamlit** (`streamlit_app.py`) for uploads and a polished review UI; **FastAPI + React** (`app/api/server.py`, `frontend/`) for an alternate demo surface. |
| **CLI** | `python -m app.main` for headless runs. |

---

## How we did it (architecture)

### Coordinator and “graph”

The file `app/orchestrator/graph.py` defines **`run_workflow(...)`**, which:

1. Resolves all paths against a **`workspace_root`** (project root when launched from the API or Streamlit, or current working directory for the CLI).  
2. Creates a unique **trace file** per run: `traces/run_<YYYYMMDDTHHMMSSZ>.jsonl`.  
3. Instantiates **`WorkflowState`** with absolute paths for bug report, logs, repo, and output directory.  
4. Appends a `workflow_start` trace event.  
5. Invokes agents **in a fixed order** (explicit handoffs — each agent reads and mutates the same `state` object):  
   **Triage → Log Analyst → Reproduction → Fix Planner → Reviewer/Critic**  
6. Serializes the final **`Final Report.json`** and appends `workflow_end` to the trace.

This is intentionally a **simple directed workflow**: same topology every time, easy to reason about and to show in a demo. The assessment text *encourages* graph/state-machine style orchestration; this project implements that idea **without** an external graph framework.

### LangGraph — not used in this codebase

**LangGraph is not a dependency here** and is **not imported** anywhere in this repository.

We chose a **small custom orchestrator** because:

- The workflow is **fixed and linear** for the assessment demo.  
- The default agents are **rule-based** (no LLM calls), so a heavy graph runtime is optional.  
- Reviewers can read **`graph.py`** top-to-bottom and see the full control flow immediately.

**How this relates to LangGraph:** LangGraph (or similar) is a natural **next step** if you add **branching** (e.g. “if repro fails, loop back to Log Analyst”), **human-in-the-loop**, or **LLM-driven** nodes. The current **`WorkflowState`** and **trace format** are deliberately compatible with that kind of migration: you would replace or wrap `run_workflow` with a LangGraph graph while keeping the same agent modules and tools.

---

## Shared state (`WorkflowState`)

Defined in `app/orchestrator/state.py`. The orchestrator and all agents read/write fields such as:

- **Inputs / run metadata:** `workspace_root`, `bug_report_path`, `logs_path`, `repo_root`, `output_dir`, `trace_path`, `run_id`  
- **Triage:** `bug_summary`, `triage_hypotheses`  
- **Logs:** `log_evidence`, `likely_failure_surface`  
- **Repro:** `repro_artifact_path`, `repro_command`, `repro_result`  
- **Planning:** `root_cause_hypothesis`, `patch_plan`, `validation_plan`  
- **Review:** `reviewer_findings`, `open_questions`, `confidence`  
- **Paths:** `final_report_path` (set when the report is written)

The **final JSON report** is a projection of these fields (see `graph.py`).

---

## Agents (roles, behavior, files)

Each agent logs **`agent_start`** and **`agent_end`** (with a small payload) to the trace file.

### 1. Triage Agent — `app/agents/triage.py`

**Role:** Parse the bug report and frame the incident.

**Behavior:** Reads the bug report file, extracts structured fields (e.g. title, description, expected vs actual, environment via line-oriented patterns), assigns a **severity** heuristic, builds **`bug_summary`**, and emits **prioritized hypotheses** in **`triage_hypotheses`**.

### 2. Log Analyst Agent — `app/agents/log_analyst.py`

**Role:** Turn raw logs into **evidence**.

**Behavior:** Uses tools to collect **error-line signatures**, **Python-style stack traces**, **version/deploy-style markers** when present, and **noise / red herring** lines to show robustness. Writes structured blocks into **`log_evidence`** and a short **`likely_failure_surface`** (module/function-style hints derived from the trace).

### 3. Reproduction Agent — `app/agents/reproduction.py`

**Role:** Produce a **runnable minimal repro** and **execute** it.

**Behavior:** Writes a Python script under **`artifacts/generated_repro/`**, then runs it with **`subprocess`** from **`workspace_root`** so imports resolve correctly. Captures **stdout/stderr**, **exit code**, and a coarse **failure signature** (e.g. `ZeroDivisionError` when present). Updates **`repro_*`** fields on state.

This satisfies the assessment requirement that **tools actually run** (not only described).

### 4. Fix Planner Agent — `app/agents/fix_planner.py`

**Role:** Propose **root cause**, **patch plan**, and **validation**.

**Behavior:** Calls **repo search** (ripgrep when available, **Python fallback** if `rg` is missing), ties **`root_cause_hypothesis`** to **repro outcome** and **log/stack excerpts**, and fills **`patch_plan`** (files, approach, risks) and **`validation_plan`** (tests to add, regression checks).

### 5. Reviewer / Critic Agent — `app/agents/reviewer.py`

**Role:** Challenge assumptions and **calibrate confidence**.

**Behavior:** Checks whether the repro **failed as expected**, whether the **stderr signature** aligns with the expected failure class, adds **severity-tagged findings**, sets **`open_questions`** (still present in JSON for assessors; hidden from Streamlit UI by product choice), and sets a scalar **`confidence`** on state (e.g. higher when fewer critic flags fire).

---

## Tools (programmatic, agent-invoked)

| Tool module | Responsibility |
|-------------|----------------|
| `app/tools/log_tools.py` | Scan logs for error-like lines; extract traceback blocks. |
| `app/tools/exec_tools.py` | Run shell commands (used to execute the generated repro). |
| `app/tools/repo_tools.py` | Search the repo (`rg` + safe regex; **fallback** directory walk if `rg` is absent). |
| `app/tools/tracing.py` | Append **JSON lines** to the run trace file. |

Agents import and call these functions directly — satisfying the requirement that **tools are invoked programmatically**.

---

## Metrics, signals, and confidence (what “numbers” mean)

The system does not ship a separate metrics server; it **emits interpretable signals** inside the report and trace:

| Signal | Where | Meaning |
|--------|--------|---------|
| **Hypothesis confidence** | `root_cause_hypothesis.confidence` (Fix Planner) | How strongly the planner states the cause (still rule-based; not a probabilistic model). |
| **Final confidence** | `confidence` (Reviewer) | **Downstream** score after critic checks (e.g. reduced if repro did not fail or signature mismatched logs). |
| **Repro exit code** | `repro.result.return_code` | Non-zero indicates the repro **failed at runtime** (expected for this demo bug). |
| **Failure signature** | `repro.result.failure_signature` | Coarse class (e.g. `ZeroDivisionError`) for alignment with logs. |
| **Error signature count** | Evidence block `error_signatures.count` | How many log lines matched error heuristics. |
| **Trace event count** | Length of `traces/run_*.jsonl` | Proxy for “how much orchestration was logged.” |

Streamlit surfaces **confidence**, **trace length**, and **repro signature** in the UI for quick scanning.

---

## Sample inputs and mini-repo (Option A)

The assessment recommends a **small codebase with an intentional bug**.

| Artifact | Path | Purpose |
|----------|------|---------|
| Bug report | `inputs/bug_report.md` | Title, expected/actual, environment, hints. |
| Logs | `inputs/logs/app.log` | Stack trace, error line, **decoy / noise** lines. |
| Mini-repo | `mini_repo/` | e.g. `calculator.py` with **`average([])`** → **`ZeroDivisionError`**. |

The **Reproduction Agent** generates a script that calls into this code path so the failure is **repeatable**.

---

## Outputs and traceability

### `artifacts/Final Report.json`

Fixed filename (**overwritten each run**): consolidates bug summary, hypotheses, failure surface, evidence, repro command/result, root cause, patch plan, validation plan, reviewer findings, open questions, and final confidence.

### `artifacts/generated_repro/repro_average_empty.py`

Regenerated when the workflow runs (path may vary if you change the agent). **Run from project root:**  
`python3 artifacts/generated_repro/repro_average_empty.py`  
You should see a **failure** consistent with the demo bug.

### `traces/run_<UTC>.jsonl`

One JSON object per line, e.g.:

- `workflow_start` / `workflow_end`  
- `agent_start` / `agent_end` (with agent name and small payloads)  

Use this file to prove **multi-agent orchestration** and **step-by-step traceability** to graders or in a demo video.

---

## Project layout

```
app/
  main.py                 # CLI entry
  orchestrator/
    graph.py              # Coordinator: run_workflow
    state.py              # WorkflowState
  agents/                 # One file per agent role
  tools/                  # Log, exec, repo, tracing helpers
  api/server.py           # FastAPI (optional)
streamlit_app.py          # Streamlit UI (optional)
frontend/                 # React + Vite (optional; build for /ui)
inputs/                   # Sample bug report + logs
mini_repo/                # Sample buggy code
artifacts/                # Final Report.json, generated repro (gitignored pieces optional)
traces/                   # Per-run JSONL traces
requirements.txt          # fastapi, uvicorn, streamlit
```

---

## Setup

**Python 3.11+** recommended.

```bash
python3 --version
```

### Core orchestrator (stdlib only)

The pipeline logic in `app/` (agents + graph + tools) uses the **standard library** only. For a minimal check:

```bash
python3 -m app.main --bug-report inputs/bug_report.md --logs inputs/logs/app.log --repo-root mini_repo --output-dir artifacts
```

### Optional dependencies (web UIs)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## How to run

### CLI (full pipeline)

```bash
python3 -m app.main \
  --bug-report inputs/bug_report.md \
  --logs inputs/logs/app.log \
  --repo-root mini_repo \
  --output-dir artifacts
```

**Expected:** repro fails with **`ZeroDivisionError`**, **`artifacts/Final Report.json`** updated, **`traces/run_<id>.jsonl`** created.

### Streamlit (recommended demo — uploads, no Node)

```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

Supports:

- **Upload** bug report (`.md` / `.json` / `.txt`) and logs (`.log` / `.txt`)  
- Optional **`.zip`** repo snapshot, or **fallback path** (e.g. `mini_repo`)  
- Structured sections (no raw JSON in the main view); download **Final Report.json** from the app  

### FastAPI + built React UI

```bash
cd frontend && npm install && npm run build && cd ..
uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000
```

- App UI: **http://127.0.0.1:8000/ui/** (redirect from `/` when built)  
- OpenAPI: **http://127.0.0.1:8000/docs**  
- Run: **`POST /api/run`** with JSON body for paths (defaults match the sample inputs).  

### FastAPI + Vite dev (hot reload)

Terminal 1: `uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000`  
Terminal 2: `cd frontend && npm run dev` → **http://127.0.0.1:5173** (proxies `/api`).

---

## Submission checklist (assessment alignment)

- [x] Multi-agent orchestration with **separate responsibilities**  
- [x] **Coordinator** + **explicit order** of agent execution  
- [x] **Programmatic tools** (log parse, search, subprocess, trace writer)  
- [x] **Minimal reproducible artifact** + **execution**  
- [x] **Structured output** (`Final Report.json`)  
- [x] **Trace file** with agent/tool-related events  
- [x] Sample **bug report**, **logs** (with stack trace + noise), **mini-repo**  
- [x] **README** with setup and run instructions  
- [x] No hard-coded secrets; optional LLM keys would belong in **environment variables** only  

---

## Extending the project

- **LangGraph / LangChain:** Swap `run_workflow` for a graph definition; keep `WorkflowState` and agent `run(state)` functions as nodes.  
- **Real LLMs:** Use env vars for API keys; constrain each agent to structured JSON outputs that still fill the same state fields.  
- **Branching:** Add conditional edges (e.g. re-run log analysis if repro passes unexpectedly).  

---

## Notes

- **`Final Report.json`** is **overwritten** on each run so the filename stays stable for demos. **Traces** remain **unique per run** (`run_<UTC>.jsonl`).  
- Secrets are **not** hard-coded.  
- This repo prioritizes **clarity, reproducibility, and engineering judgment** over framework buzzwords; the design maps cleanly to the assessment rubric.
