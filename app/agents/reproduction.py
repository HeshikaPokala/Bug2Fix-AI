from __future__ import annotations

import re
from pathlib import Path

from app.orchestrator.state import WorkflowState
from app.tools import llm_tools
from app.tools.exec_tools import run_command
from app.tools.repo_tools import read_source_snippet
from app.tools.tracing import append_trace

# The probe script tries 0-2 LLM-proposed candidates first (an initial guess, then
# one retry informed by what the initial guess actually raised), then falls back to
# a fixed bag of edge-case guesses (repeated across every parameter) -- generalizes
# to any function-level bug reproducible by *some* edge case, LLM-assisted or not.
_REPRO_TEMPLATE = '''from __future__ import annotations

import importlib
import inspect
import sys

sys.path.insert(0, {workspace_root!r})

MODULE_NAME = {module_name!r}
FUNCTION_NAME = {function_name!r}
EXPECTED_ERROR = {expected_error!r}
LLM_CANDIDATES = {llm_candidates!r}
INCLUDE_FALLBACK = {include_fallback!r}

FALLBACK_VALUES = [
    ([], "empty list"),
    (None, "None"),
    (0, "zero"),
    ("", "empty string"),
    ({{}}, "empty dict"),
    (-1, "negative number"),
]


def main() -> None:
    module = importlib.import_module(MODULE_NAME)
    func = getattr(module, FUNCTION_NAME)
    arity = len(inspect.signature(func).parameters)

    candidates: list[tuple[list, str]] = list(LLM_CANDIDATES)
    if INCLUDE_FALLBACK:
        fallback_source = FALLBACK_VALUES if arity > 0 else FALLBACK_VALUES[:1]
        candidates.extend(([value] * arity, label) for value, label in fallback_source)

    for args, label in candidates:
        print(f"--- trying input={{label}} ({{args!r}}) ---")
        try:
            result = func(*args)
            print(f"no error, result={{result!r}}")
        except Exception as exc:  # noqa: BLE001 - intentionally broad, this is a probe
            error_type = type(exc).__name__
            print(f"{{error_type}}: {{exc}}")
            if error_type == EXPECTED_ERROR:
                print(f"REPRO_MATCH input={{label}} error={{error_type}}")
                raise


if __name__ == "__main__":
    main()
'''


def _module_import_name(resolved_path: str, workspace_root: Path) -> str | None:
    try:
        rel = Path(resolved_path).resolve().relative_to(workspace_root.resolve())
    except ValueError:
        return None
    if rel.suffix != ".py":
        return None
    return ".".join(rel.with_suffix("").parts)


def _split_top_level(params_str: str) -> list[str]:
    """Split a parameter-list string on top-level commas, respecting bracket depth
    and string literals (so `dict[str, float]` and default value `'x,y'` don't get
    mistaken for parameter separators).
    """
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote_char: str | None = None
    for ch in params_str:
        if quote_char is not None:
            current.append(ch)
            if ch == quote_char:
                quote_char = None
            continue
        if ch in "'\"":
            quote_char = ch
            current.append(ch)
        elif ch in "([{":
            depth += 1
            current.append(ch)
        elif ch in ")]}":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def _extract_params(function_name: str, source: str) -> list[dict[str, str | None]] | None:
    """Best-effort parameter name + type extraction from the `def` line. Not a
    substitute for real introspection (which happens at runtime in the probe
    script) -- used to ask the LLM for a *named*, per-parameter-typed answer
    (`{"catalog": {...}, "sku": "..."}`) instead of a positional list, since a
    positional list gave the model no way to signal which value goes in which
    typed slot and it silently mixed them up on multi-argument, differently-typed
    functions (see demo/README.md's `llm_dict_key` category).
    """
    match = re.search(rf"def\s+{re.escape(function_name)}\s*\(([^)]*)\)", source)
    if not match:
        return None
    params_str = match.group(1).strip()
    if not params_str:
        return []
    params = []
    for segment in _split_top_level(params_str):
        name_and_type = segment.split("=", 1)[0].strip()  # drop any default value
        if ":" in name_and_type:
            name, type_hint = name_and_type.split(":", 1)
            params.append({"name": name.strip(), "type": type_hint.strip()})
        else:
            params.append({"name": name_and_type.strip(), "type": None})
    return params


def _estimate_arity(function_name: str, source: str) -> int | None:
    params = _extract_params(function_name, source)
    return len(params) if params is not None else None


def _validate_named_args(args: object, params: list[dict[str, str | None]]) -> list | None:
    """Validates a {param_name: value} object against the known parameter list and
    converts it to the ordered positional list the probe script actually calls the
    function with. Requires every parameter name to be present (exact match) --
    a partial or misspelled response is treated the same as no answer.
    """
    if not isinstance(args, dict):
        return None
    ordered = []
    for param in params:
        name = param["name"]
        if name not in args:
            return None
        ordered.append(args[name])
    return ordered


def _param_prompt_block(params: list[dict[str, str | None]]) -> tuple[str, str]:
    lines = "\n".join(f"- {p['name']}: {p['type'] or 'unspecified type'}" for p in params)
    example_keys = ", ".join(f'"{p["name"]}": <value>' for p in params)
    return lines, example_keys


def _llm_propose_args(function_name: str, source: str, bug_title: str, expected_error: str) -> list | None:
    if not source:
        return None
    params = _extract_params(function_name, source)
    if not params:
        return [] if params == [] else None
    param_lines, example_keys = _param_prompt_block(params)
    prompt = (
        "You are helping reproduce a Python bug by choosing input values to call a function with.\n\n"
        f"Bug report title: {bug_title}\n"
        f"Function to call: {function_name}\n"
        f"Logs indicate this function raised: {expected_error}\n\n"
        "Function source:\n```python\n" + source + "\n```\n\n"
        f"The function's parameters, in order, are:\n{param_lines}\n\n"
        'Return ONLY JSON of the shape {"args": {' + example_keys + '}} -- a JSON OBJECT '
        "keyed by the exact parameter names listed above, one key per parameter, each "
        "mapped to a value of the type stated for that parameter. Do NOT return a list/array "
        'for "args" -- it must be an object so each value is unambiguously matched to its '
        "parameter by name, not by position.\n"
        f"Choose values you believe would make the function raise {expected_error}."
    )
    try:
        result = llm_tools.generate_json(prompt)
    except llm_tools.OllamaUnavailable:
        return None
    return _validate_named_args(result.get("args"), params)


def _llm_propose_args_retry(
    function_name: str,
    source: str,
    bug_title: str,
    expected_error: str,
    previous_args: list,
    previous_outcome: str,
) -> list | None:
    if not source:
        return None
    params = _extract_params(function_name, source)
    if not params:
        return None
    param_lines, example_keys = _param_prompt_block(params)
    previous_named = {p["name"]: v for p, v in zip(params, previous_args)}
    prompt = (
        "You are helping reproduce a Python bug by choosing input values to call a function with.\n\n"
        f"Bug report title: {bug_title}\n"
        f"Function to call: {function_name}\n"
        f"Logs indicate this function should raise: {expected_error}\n\n"
        "Function source:\n```python\n" + source + "\n```\n\n"
        f"The function's parameters, in order, are:\n{param_lines}\n\n"
        f"Your previous attempt called the function with {previous_named!r}, but that "
        f"produced: {previous_outcome}\n"
        "That did not reproduce the expected error. Look carefully at each parameter's "
        "declared type above, and at why your previous guess was wrong (e.g. a value of "
        "the wrong type for one of the parameters, or a value that doesn't actually "
        "trigger this specific bug), then propose a corrected input.\n\n"
        'Return ONLY JSON of the shape {"args": {' + example_keys + '}} -- a JSON OBJECT '
        "keyed by the exact parameter names listed above, each mapped to a value of the "
        "stated type for that parameter.\n"
        f"Choose values you believe would make the function raise {expected_error}."
    )
    try:
        result = llm_tools.generate_json(prompt)
    except llm_tools.OllamaUnavailable:
        return None
    return _validate_named_args(result.get("args"), params)


def _write_script(
    path: Path,
    workspace_root: Path,
    module_name: str,
    function_name: str,
    expected_error: str,
    llm_candidates: list[tuple[list, str]],
    include_fallback: bool,
) -> None:
    script = _REPRO_TEMPLATE.format(
        workspace_root=str(workspace_root),
        module_name=module_name,
        function_name=function_name,
        expected_error=expected_error,
        llm_candidates=llm_candidates,
        include_fallback=include_fallback,
    )
    path.write_text(script, encoding="utf-8")


def _run_script(path: Path, workspace_root: Path) -> dict:
    result = run_command(["python3", str(path)], cwd=workspace_root)
    return {"return_code": result["return_code"], "stdout": str(result["stdout"]), "stderr": str(result["stderr"])}


def _matched(stderr: str, expected_error: str) -> bool:
    return expected_error != "unknown" and expected_error in stderr


def _last_attempt_outcome(stdout: str) -> str:
    """Pull the outcome line (error or 'no error') from a single-candidate trial run,
    to hand back to the LLM as concrete feedback for its retry.
    """
    lines = [line for line in stdout.strip().splitlines() if line.strip() and not line.startswith("---")]
    return lines[-1] if lines else "no output captured (the call may have hung or produced nothing)"


def run(state: WorkflowState) -> None:
    append_trace(state.trace_path, "agent_start", {"agent": "ReproductionAgent"})
    surface = state.likely_failure_surface
    module_name = None
    if surface.get("resolved_path"):
        module_name = _module_import_name(surface["resolved_path"], state.workspace_root)

    if not module_name or surface.get("function") in (None, "unknown"):
        state.repro_artifact_path = ""
        state.repro_command = ""
        state.repro_result = {
            "failed_consistently": False,
            "return_code": None,
            "stdout": "",
            "stderr": "",
            "failure_signature": "unknown",
            "trigger_input": None,
            "llm_assisted": False,
            "llm_attempts": 0,
            "note": "Could not resolve a failing function from the logs to synthesize a reproduction.",
        }
        append_trace(state.trace_path, "agent_end", {"agent": "ReproductionAgent", "status": "skipped_unresolved"})
        return

    function_name = surface["function"]
    expected_error = surface.get("error_type", "unknown")
    bug_title = state.bug_summary.get("title", "")
    repro_dir = state.output_dir / "generated_repro"
    repro_dir.mkdir(parents=True, exist_ok=True)

    llm_candidates: list[tuple[list, str]] = []
    llm_attempts = 0
    use_llm = state.use_llm and llm_tools.is_available()

    if use_llm:
        source = read_source_snippet(surface.get("resolved_path", ""))
        args1 = _llm_propose_args(function_name, source, bug_title, expected_error)
        if args1 is not None:
            llm_attempts = 1
            trial_path = repro_dir / f"repro_{state.run_id}_attempt1.py"
            _write_script(trial_path, state.workspace_root, module_name, function_name, expected_error, [(args1, "llm attempt 1")], include_fallback=False)
            trial = _run_script(trial_path, state.workspace_root)

            if _matched(trial["stderr"], expected_error):
                llm_candidates = [(args1, "llm attempt 1")]
            else:
                outcome = _last_attempt_outcome(trial["stdout"])
                args2 = _llm_propose_args_retry(function_name, source, bug_title, expected_error, args1, outcome)
                if args2 is not None:
                    llm_attempts = 2
                    trial2_path = repro_dir / f"repro_{state.run_id}_attempt2.py"
                    _write_script(trial2_path, state.workspace_root, module_name, function_name, expected_error, [(args2, "llm attempt 2 (retry)")], include_fallback=False)
                    trial2 = _run_script(trial2_path, state.workspace_root)
                    if _matched(trial2["stderr"], expected_error):
                        llm_candidates = [(args2, "llm attempt 2 (retry)")]
                    else:
                        # Neither attempt reproduced it -- still include both in the final
                        # script (in original order) so the artifact shows everything tried.
                        llm_candidates = [(args1, "llm attempt 1"), (args2, "llm attempt 2 (retry)")]
                else:
                    llm_candidates = [(args1, "llm attempt 1")]

    repro_path = repro_dir / f"repro_{state.run_id}.py"
    _write_script(repro_path, state.workspace_root, module_name, function_name, expected_error, llm_candidates, include_fallback=True)
    result = _run_script(repro_path, state.workspace_root)
    stdout, stderr = result["stdout"], result["stderr"]

    trigger_input = next((line for line in stdout.splitlines() if line.startswith("REPRO_MATCH")), None)
    matched = _matched(stderr, expected_error)
    matched_via_llm = matched and trigger_input is not None and "llm attempt" in trigger_input

    try:
        display_path = repro_path.relative_to(state.workspace_root)
    except ValueError:
        display_path = repro_path

    state.repro_artifact_path = str(repro_path)
    state.repro_command = f"python3 {display_path}"
    state.repro_result = {
        "failed_consistently": result["return_code"] != 0 and matched,
        "return_code": result["return_code"],
        "stdout": stdout,
        "stderr": stderr,
        "failure_signature": expected_error if matched else "unknown",
        "trigger_input": trigger_input,
        "llm_assisted": matched_via_llm,
        "llm_attempts": llm_attempts,
    }
    append_trace(
        state.trace_path,
        "agent_end",
        {
            "agent": "ReproductionAgent",
            "artifact": state.repro_artifact_path,
            "return_code": result["return_code"],
            "matched_expected_error": matched,
            "llm_attempts": llm_attempts,
            "matched_via_llm": matched_via_llm,
        },
    )
