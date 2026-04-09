"""
Streamlit UI for the bug-triage orchestrator.

Run from project root:
  streamlit run streamlit_app.py
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
import zipfile

import streamlit as st

from app.orchestrator.graph import run_workflow

PROJECT_ROOT = Path(__file__).resolve().parent
UPLOADS_ROOT = PROJECT_ROOT / "runtime_inputs"


def _ts() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _read_trace_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _save_uploaded(upload, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(upload.getbuffer())


def _find_repo_root(extracted_dir: Path) -> Path:
    if any(extracted_dir.glob("*.py")):
        return extracted_dir
    children = [p for p in extracted_dir.iterdir() if p.is_dir()]
    for child in children:
        if any(child.rglob("*.py")):
            return child
    return extracted_dir


def _render_bug_summary(bs: dict) -> None:
    if not bs:
        st.warning("No bug summary produced.")
        return
    st.markdown(f"### {bs.get('title', 'Untitled')}")
    sev = bs.get("severity", "—")
    st.markdown(f"**Severity:** `{sev}`  \n**Scope:** {bs.get('scope', '—')}")
    if bs.get("symptoms"):
        st.markdown("**Symptoms / description**")
        st.write(bs["symptoms"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Expected behavior**")
        st.info(bs.get("expected_behavior", "—") or "—")
    with c2:
        st.markdown("**Actual behavior**")
        st.error(bs.get("actual_behavior", "—") or "—")
    st.markdown("**Environment**")
    st.code(bs.get("environment", "—") or "—", language="text")


def _render_hypotheses(hypotheses: list) -> None:
    if not hypotheses:
        return
    st.markdown("**Prioritized hypotheses (Triage Agent)**")
    for h in hypotheses:
        hid = h.get("id", "?")
        pri = h.get("priority", "?")
        st.markdown(f"- **{hid}** (priority {pri}): {h.get('hypothesis', '')}")


def _render_failure_surface(fs: dict) -> None:
    if not fs:
        st.caption("No failure surface struct from Log Analyst.")
        return
    st.markdown(
        f"- **Module / file:** `{fs.get('module', 'unknown')}`  \n"
        f"- **Function / symbol:** `{fs.get('function', 'unknown')}`  \n"
        f"- **Reasoning:** {fs.get('reason', '—')}"
    )


def _render_evidence_block(block: dict) -> None:
    btype = block.get("type", "evidence")
    title = btype.replace("_", " ").title()

    if btype == "error_signatures":
        count = block.get("count", 0)
        st.markdown(f"**Count:** {count}")
        items = block.get("items") or []
        if not items:
            st.caption("No matching lines (unexpected if logs contain errors).")
            return
        rows = [{"Log line": it.get("line", "—"), "Snippet": it.get("text", "")[:500]} for it in items]
        st.dataframe(rows, use_container_width=True, hide_index=True)

    elif btype == "stack_trace":
        lines = block.get("lines") or []
        if not lines:
            st.caption("No Python-style traceback block found in logs.")
            return
        st.code("\n".join(lines), language="text")

    elif btype == "correlated_versions":
        items = block.get("items") or []
        vals = [it.get("text") for it in items if it.get("text")]
        if not vals:
            st.caption("No version / deploy markers matched in this log sample.")
            return
        for v in vals:
            st.markdown(f"- `{v}`")

    elif btype == "noise_red_herrings":
        st.caption("Lines treated as noise / red herrings for robustness (still shown).")
        items = block.get("items") or []
        if not items:
            st.caption("None detected with current heuristics.")
            return
        for it in items:
            st.markdown(f"- {it.get('text', '')}")

    else:
        st.write(block)


def _render_patch_plan(pp: dict) -> None:
    if not pp:
        return
    st.markdown("**Files / modules impacted**")
    for f in pp.get("files_impacted", []):
        st.code(f, language="text")
    st.markdown("**Approach**")
    for i, step in enumerate(pp.get("approach", []), 1):
        st.markdown(f"{i}. {step}")
    st.markdown("**Risks**")
    for r in pp.get("risks", []):
        st.warning(r)


def _render_validation(vp: dict) -> None:
    if not vp:
        return
    st.markdown("**Tests to add**")
    for t in vp.get("tests_to_add", []):
        st.markdown(f"- `{t}`")
    st.markdown("**Regression checks**")
    for r in vp.get("regression_checks", []):
        st.markdown(f"- {r}")


def _render_trace_timeline(trace: list[dict]) -> None:
    for ev in trace:
        ts = ev.get("ts", "")[:19].replace("T", " ")
        kind = ev.get("event", "")
        payload = ev.get("payload", {})
        agent = payload.get("agent")
        if agent:
            line = f"**{ts}** · `{kind}` · **{agent}**"
        else:
            line = f"**{ts}** · `{kind}`"
        st.markdown(line)
        if payload:
            parts = [f"{k}={payload[k]}" for k in sorted(payload.keys()) if k != "agent"]
            if parts:
                st.caption(" · ".join(str(p) for p in parts[:6]))


def _inject_theme_css() -> None:
    st.markdown(
        """
<style>
  /* App shell — light */
  .stApp {
    background: radial-gradient(1000px 480px at 50% -8%, rgba(124, 58, 237, 0.06), transparent),
                linear-gradient(180deg, #ffffff 0%, #f8fafc 45%, #f1f5f9 100%);
    color: #334155;
  }
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
    border-right: 1px solid #e2e8f0;
  }
  section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
  }
  .main .block-container {
    padding-top: 1.75rem;
    padding-bottom: 3rem;
    max-width: 72rem;
  }
  /* Body copy */
  .main [data-testid="stMarkdown"] p,
  .main [data-testid="stMarkdown"] li {
    color: #334155;
  }
  /* Typography */
  h1 {
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #0f172a !important;
    margin-bottom: 0.35rem !important;
  }
  h2, h3 {
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #1e293b !important;
    margin-top: 0.25rem !important;
    margin-bottom: 0.65rem !important;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid #e2e8f0;
  }
  .stCaption, [data-testid="caption"] {
    color: #64748b !important;
  }
  /* Metrics as cards */
  [data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    padding: 0.85rem 1rem !important;
    min-height: 5.5rem;
  }
  [data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-size: 0.8rem !important;
    text-transform: none;
    letter-spacing: 0.01em;
  }
  [data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-size: 1.5rem !important;
    font-weight: 600 !important;
  }
  /* Inputs */
  section[data-testid="stSidebar"] label {
    color: #475569 !important;
    font-size: 0.85rem !important;
  }
  .stRadio label, .stTextInput label, .stFileUploader label {
    color: #334155 !important;
  }
  div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border-color: #cbd5e1 !important;
    border-radius: 8px !important;
  }
  /* Primary button */
  .stButton button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.55rem 1rem !important;
    color: #ffffff !important;
    box-shadow: 0 6px 20px -6px rgba(124, 58, 237, 0.45);
  }
  .stButton button[kind="primary"]:hover {
    filter: brightness(1.05);
  }
  /* Alerts */
  div[data-testid="stAlert"] {
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
  }
  /* Expanders */
  [data-testid="stExpander"] details {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  }
  [data-testid="stExpander"] summary {
    font-weight: 500 !important;
    color: #1e293b !important;
  }
  [data-testid="stExpander"] summary:hover {
    color: #0f172a !important;
  }
  /* Code */
  .stCodeBlock, pre {
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #f8fafc !important;
  }
  /* Dataframe */
  div[data-testid="stDataFrame"] {
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    background: #ffffff;
  }
  /* Progress */
  .stProgress > div > div {
    background: linear-gradient(90deg, #7c3aed, #22d3ee) !important;
    border-radius: 999px;
  }
  /* Hypothesis confidence label — white on purple/cyan track */
  [data-testid="stProgress"] {
    color: #ffffff !important;
  }
  [data-testid="stProgress"] p,
  [data-testid="stProgress"] span,
  [data-testid="stProgress"] label,
  [data-testid="stProgress"] > div > div:first-child {
    color: #ffffff !important;
    font-weight: 600 !important;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
  }
  [data-baseweb="progress-bar"] {
    color: #ffffff !important;
  }
  /* Output paths footer — size + font aligned with main UI */
  .wm-output-paths {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-top: 0.85rem;
    padding-top: 0.75rem;
    border-top: 1px solid #e2e8f0;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 0.875rem;
  }
  .wm-output-paths .wm-path-label {
    font-size: 0.8125rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 0.25rem;
  }
  .wm-output-paths .wm-path-value {
    display: block;
    font-size: 0.8125rem;
    line-height: 1.45;
    font-family: inherit;
    font-weight: 400;
    color: #334155;
    background: #f8fafc;
    padding: 0.45rem 0.6rem;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    word-break: break-all;
  }
  @media (max-width: 768px) {
    .wm-output-paths {
      grid-template-columns: 1fr;
    }
  }
  /* Dividers */
  hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 1.25rem 0;
  }
  /* Bordered containers (Streamlit) */
  div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 14px !important;
    padding: 1rem 1.15rem 1.15rem !important;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  }
  /* Download */
  .stDownloadButton button {
    border-radius: 10px !important;
    border: 1px solid #c4b5fd !important;
    background: #f5f3ff !important;
    color: #5b21b6 !important;
    font-weight: 500 !important;
  }
  .stDownloadButton button:hover {
    background: #ede9fe !important;
    border-color: #a78bfa !important;
  }
</style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Agent War Room",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

_inject_theme_css()

st.title("Agent War Room")
st.caption("Upload bug report + logs (+ optional repo snapshot zip), then run deterministic multi-agent analysis.")

with st.sidebar:
    st.header("Inputs")
    mode = st.radio("Input mode", ["Upload files", "Use paths"], horizontal=False)

    if mode == "Upload files":
        bug_report_upload = st.file_uploader(
            "Bug report (Markdown or JSON)",
            type=["md", "txt", "json"],
            accept_multiple_files=False,
        )
        logs_upload = st.file_uploader(
            "Logs (plain text)",
            type=["log", "txt"],
            accept_multiple_files=False,
        )
        repo_zip_upload = st.file_uploader(
            "Optional repository snapshot (.zip)",
            type=["zip"],
            accept_multiple_files=False,
        )
        fallback_repo = st.text_input(
            "Fallback repo path (used if no zip provided)",
            "mini_repo",
        )
        output_dir_str = st.text_input("Output dir", "artifacts")
    else:
        bug_report_path_str = st.text_input("Bug report path", "inputs/bug_report.md")
        logs_path_str = st.text_input("Logs path", "inputs/logs/app.log")
        repo_path_str = st.text_input("Repo root path", "mini_repo")
        output_dir_str = st.text_input("Output dir", "artifacts")

    run_btn = st.button("Run full analysis", type="primary", use_container_width=True)

st.markdown(
    """
<div style="color:#64748b;font-size:0.95rem;line-height:1.55;padding:0.65rem 0 0.25rem 0;">
<strong style="color:#1e293b;">Pipeline:</strong>
parse inputs → triage → log evidence → minimal repro (run) → root cause + patch plan → critic review.
</div>
""",
    unsafe_allow_html=True,
)

if run_btn:
    with st.spinner("Running TriageAgent → LogAnalystAgent → ReproductionAgent → FixPlannerAgent → ReviewerCriticAgent..."):
        try:
            if mode == "Upload files":
                if not bug_report_upload or not logs_upload:
                    st.error("Please upload both bug report and logs.")
                    st.stop()

                run_dir = UPLOADS_ROOT / f"run_{_ts()}"
                bug_path = run_dir / "bug_report" / bug_report_upload.name
                logs_path = run_dir / "logs" / logs_upload.name
                _save_uploaded(bug_report_upload, bug_path)
                _save_uploaded(logs_upload, logs_path)

                if repo_zip_upload:
                    repo_zip_path = run_dir / "repo_snapshot.zip"
                    _save_uploaded(repo_zip_upload, repo_zip_path)
                    extract_dir = run_dir / "repo_snapshot"
                    extract_dir.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(repo_zip_path, "r") as zf:
                        zf.extractall(extract_dir)
                    repo_root = _find_repo_root(extract_dir)
                else:
                    repo_root = Path(fallback_repo)

                result = run_workflow(
                    bug_report_path=bug_path,
                    logs_path=logs_path,
                    repo_root=repo_root,
                    output_dir=Path(output_dir_str),
                    workspace_root=PROJECT_ROOT,
                )
            else:
                result = run_workflow(
                    bug_report_path=Path(bug_report_path_str),
                    logs_path=Path(logs_path_str),
                    repo_root=Path(repo_path_str),
                    output_dir=Path(output_dir_str),
                    workspace_root=PROJECT_ROOT,
                )

            report_path = Path(result["final_report_path"])
            trace_path = Path(result["trace_path"])
            report = json.loads(report_path.read_text(encoding="utf-8"))
            trace = _read_trace_jsonl(trace_path)
            st.session_state["last_run"] = {
                "result": result,
                "report": report,
                "trace": trace,
            }
        except Exception as e:
            st.error(str(e))
            st.stop()

if "last_run" not in st.session_state:
    st.info("Upload your inputs (or use paths) and click Run full analysis.")
    st.stop()

data = st.session_state["last_run"]
report = data["report"]
trace = data["trace"]
paths = data["result"]

conf = float(report.get("confidence", 0) or 0)
with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    c1.metric("Confidence", f"{conf * 100:.0f}%")
    c2.metric("Trace events", len(trace))
    c3.metric("Report file", Path(paths["final_report_path"]).name)

st.subheader("Agent pipeline status")
agents = [
    "TriageAgent",
    "LogAnalystAgent",
    "ReproductionAgent",
    "FixPlannerAgent",
    "ReviewerCriticAgent",
]
done = {
    a: any(
        evt.get("event") == "agent_end" and evt.get("payload", {}).get("agent") == a
        for evt in trace
    )
    for a in agents
}
with st.container(border=True):
    cols = st.columns(len(agents))
    for col, a in zip(cols, agents):
        col.metric(a.replace("Agent", "").strip() or a, "Done" if done[a] else "—")

left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.subheader("Bug summary")
        _render_bug_summary(report.get("bug_summary") or {})
        _render_hypotheses(report.get("triage_hypotheses") or [])

with right:
    with st.container(border=True):
        st.subheader("Most likely failure surface (Log Analyst)")
        _render_failure_surface(report.get("likely_failure_surface") or {})
        st.divider()
        st.markdown("**Reproduction failure signature**")
        sig = (report.get("repro") or {}).get("result", {}).get("failure_signature")
        st.code(str(sig or "unknown"), language="text")

with st.container(border=True):
    st.subheader("Reproduction artifact + result")
    repro = report.get("repro") or {}
    st.info(
        "The **Reproduction Agent** writes a small Python script under `artifacts/generated_repro/` and runs it. "
        "The command below is what you would run **from the project root** to repeat the same failure locally "
        "(same as the agent’s subprocess)."
    )
    st.markdown("**Command (from project root)**")
    st.code(repro.get("command", "") or "—", language="bash")
    if repro.get("steps"):
        st.markdown("**What I Tried:**")
        for s in repro["steps"]:
            st.markdown(f"- {s}")
    st.markdown(f"**Generated file path:** `{repro.get('artifact_path', '')}`")
    res = repro.get("result") or {}
    rc = res.get("return_code", "—")
    st.markdown(f"**Exit code:** `{rc}` (non-zero means the repro failed as intended)")
    out = str(res.get("stderr") or res.get("stdout") or "").strip()
    st.markdown("**Console output**")
    st.code(out or "(no output captured)", language="text")

st.subheader("Evidence extracted from logs")
with st.container(border=True):
    for block in report.get("evidence", []):
        with st.expander(block.get("type", "evidence").replace("_", " ").title(), expanded=True):
            _render_evidence_block(block)

col_a, col_b = st.columns(2, gap="large")
with col_a:
    with st.container(border=True):
        st.subheader("Root cause hypothesis")
        hyp = report.get("root_cause_hypothesis") or {}
        st.write(hyp.get("statement", "—"))
        hc = hyp.get("confidence")
        if hc is not None:
            st.progress(float(hc), text=f"Hypothesis confidence: {float(hc) * 100:.0f}%")
        st.markdown("**Supporting evidence**")
        for ev in hyp.get("supporting_evidence", []) or []:
            st.markdown(f"- {ev}")

with col_b:
    with st.container(border=True):
        st.subheader("Patch plan")
        _render_patch_plan(report.get("patch_plan") or {})

with st.container(border=True):
    st.subheader("Validation plan")
    _render_validation(report.get("validation_plan") or {})

with st.container(border=True):
    st.subheader("Reviewer / critic")
    for f in report.get("reviewer_critic_findings", []) or []:
        sev = (f.get("severity") or "low").lower()
        if sev == "high":
            st.error(f"**{sev.upper()}** — {f.get('issue', '')}")
        elif sev == "medium":
            st.warning(f"**{sev.upper()}** — {f.get('issue', '')}")
        else:
            st.info(f"**{sev.upper()}** — {f.get('issue', '')}")

with st.expander("Orchestration trace (timeline)", expanded=False):
    with st.container(border=True):
        _render_trace_timeline(trace)

st.download_button(
    label="Download Final Report (JSON)",
    data=json.dumps(report, indent=2),
    file_name="Final Report.json",
    mime="application/json",
)
report_fp = html.escape(str(paths["final_report_path"]))
trace_fp = html.escape(str(paths["trace_path"]))
st.markdown(
    f"""
<div class="wm-output-paths">
  <div>
    <div class="wm-path-label">Report:</div>
    <span class="wm-path-value">{report_fp}</span>
  </div>
  <div>
    <div class="wm-path-label">Trace:</div>
    <span class="wm-path-value">{trace_fp}</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)
