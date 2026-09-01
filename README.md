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

> The pipeline is fully deterministic and rule-based by default — no API keys or LLM dependency required. Two steps (Reproduction and Fix Planner) can optionally be augmented by a local Ollama model (`phi4-mini` by default): the model proposes/reasons, the deterministic path is the automatic fallback if Ollama is unavailable or its answer doesn't check out. See [Ollama-assisted mode](#ollama-assisted-mode-optional) below.

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
- Introspects the failing function's signature and generates a minimal repro script (`artifacts/generated_repro/`) that calls it with a candidate input  
- If Ollama is available, asks it to propose the input first — as a JSON object keyed by parameter name (`{"catalog": {...}, "sku": "..."}`), not a positional list, since a positional list let the model silently swap values between differently-typed argument slots (see `demo/README.md`'s "positional vs named JSON args" writeup) — grounded in the actual function source and each parameter's declared type, gets one retry-with-feedback if that guess doesn't reproduce the logged error, then falls back to a fixed set of edge-case guesses (empty list, `None`, zero, empty string, empty dict, negative number)  
- Executes the script using subprocess  
- Captures stdout, stderr, exit code, and failure signature — `failed_consistently` is only `true` if the *expected* exception type was actually raised, not just any exception  

---

### Fix Planner
- Searches the repo (via ripgrep or fallback) for the resolved function  
- If Ollama is available, asks it for a root-cause statement + patch plan grounded in the function's source; otherwise (or if the LLM's answer is malformed) falls back to a small set of templates keyed by exception type, with a generic default for unrecognized types  
- Produces:
  - Root cause hypothesis (tagged `"source": "llm"` or `"source": "rule_based"`)
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
- **repo_tools.py** — repo search (rg or fallback), source-snippet reading  
- **tracing.py** — structured JSONL logging  
- **llm_tools.py** — thin Ollama client (`generate_json`, `is_available`); every caller catches `OllamaUnavailable` and falls back to the deterministic path  

> Tools are directly invoked in code — no simulated tool-calling via prompts.

---

## Sample bugs and the eval suite

`inputs/` has the original demo bug (`average([])` → `ZeroDivisionError` in `mini_repo/calculator.py`) plus a second, deliberately different one (`first_active_user([])` → `IndexError` in `mini_repo/users.py`) used early on to prove the pipeline generalizes rather than being hardcoded to one bug — the much larger, systematic version of that same proof is `demo/`.

`demo/` has a **30-bug eval set across 6 categories** — 12 bugs solvable by the deterministic fallback alone (empty list / `None` / etc.), and 18 that genuinely require Ollama to reason about a specific, non-trivial input (a real dict + missing key, a numeric threshold, a relational check, wraparound-aware bounds, a string-length constraint). Bugs 10-30 are generated from a data catalog ([scripts/bug_catalog.py](scripts/bug_catalog.py)), not hand-written file-by-file. Each bug is a bug report + synthetic log + a small buggy function added to `mini_repo/`. See [demo/README.md](demo/README.md) for the full write-up — it documents a complete diagnose → isolate → fix → verify cycle: a systematic 0/4 failure on dict-key argument bugs was found, a **cross-model comparison against `qwen2.5-coder:7b`** (2x the size, code-specialized) showed the *identical* failure in both models (ruling out "model too small"/"model doesn't know code"), which pointed at *how* the model was asked (a positional JSON array gives it no way to bind values to differently-typed argument slots) rather than *which* model — switching to a named, per-parameter-typed JSON object closed the gap from 0/4 to 4/4 in **both** models, taking the overall score from 24/30 to **29/30**.

Run the whole set and regenerate the summary table:
```bash
python3 scripts/run_eval_suite.py           # both --no-llm and Ollama-assisted passes
python3 scripts/run_eval_suite.py --skip-llm  # deterministic only, fast, no Ollama needed
OLLAMA_MODEL="qwen2.5-coder:7b" python3 scripts/run_eval_suite.py  # cross-model comparison
```
Latest results (stable across 3 independent full runs — zero bugs flipped): **diagnosis correct 30/30**, **repro confirmed 12/30 deterministic-only vs 29/30 (96.7%) with Ollama** — see `demo/results/eval_summary.md`. Read that as 12/30 solved either way, 17/30 solved *only* because of Ollama (the fallback provably can't reach these), and 1/30 unsolved even with Ollama — not as "29 vs 12" independently.

---

## Ollama-assisted mode (optional)

Reproduction and Fix Planner can call a local Ollama model (`phi4-mini:latest` by default — `OLLAMA_MODEL` / `OLLAMA_HOST` env vars to change it). It's opt-out, not opt-in:
- CLI: `--no-llm`
- API: `"use_llm": false` in the `/api/run` request body
- Streamlit: the "Use Ollama for reasoning" checkbox

If Ollama isn't running, or its answer doesn't validate (missing a required parameter name, malformed JSON, doesn't reproduce the logged error), the pipeline silently falls back to the deterministic path — it never crashes or blocks on the LLM being unavailable. Every LLM-influenced field in the final report is tagged `"source": "llm"` or `"source": "rule_based"` so it's always clear which path actually produced it.

---

## Tests

```bash
python3 -m unittest discover -s tests -v
```
All deterministic (no Ollama, no network) — covers log parsing/frame resolution, arity estimation, template selection, reviewer confidence logic, and full end-to-end runs against the demo bugs (including a regression guard that two different bugs must produce two different diagnoses — the specific failure mode of the original hardcoded version of this project).

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
demo/           # 30-bug eval set: bug_reports/, logs/, results/, README.md
scripts/        # bug_catalog.py, generate_demo_bugs.py, run_eval_suite.py
tests/          # unittest suite (34 tests), no Ollama/network required
artifacts/      # generated per run, gitignored
traces/         # generated per run, gitignored
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

### FastAPI + React

```
uvicorn app.api.server:app --reload
```
`POST /api/run` takes `bug_report` / `logs` / `repo_root` / `output_dir` as paths and `use_llm` as a bool. Every path is resolved and checked against the project root before use (`_safe_project_path` in `app/api/server.py`) — a request can't read files outside the project directory via `..` traversal or an absolute path elsewhere, even though the endpoint accepts arbitrary path strings.

---

## Key Idea

This system is designed to mirror how engineers debug issues in practice:

- Start with incomplete information  
- Extract signal from noisy logs  
- Validate assumptions via reproduction  
- Propose fixes grounded in evidence  

It prioritizes **clarity, traceability, and determinism** over abstraction.
