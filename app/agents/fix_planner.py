from __future__ import annotations

from app.orchestrator.state import WorkflowState
from app.tools import llm_tools
from app.tools.repo_tools import read_source_snippet, repo_search
from app.tools.tracing import append_trace

# Templated patch guidance keyed by exception type -- generalizes the fix plan
# across any error we can identify, instead of a single hardcoded average()/
# ZeroDivisionError plan. Unrecognized error types fall back to a generic template.
_ERROR_PATCH_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "ZeroDivisionError": {
        "approach": [
            "Add a guard clause returning a safe default (or raising a domain-specific error) when the divisor/collection is empty.",
            "Add unit tests covering empty, single-value, and multi-value inputs.",
        ],
        "risks": [
            "A silent default may hide upstream data issues that should surface as errors.",
            "Behavioral change could affect callers that currently rely on the exception being raised.",
        ],
    },
    "KeyError": {
        "approach": [
            "Use `.get(key, default)` or an explicit membership check instead of direct indexing.",
            "Add unit tests covering missing keys and empty mappings.",
        ],
        "risks": [
            "A default value may mask a genuinely missing/required key upstream.",
        ],
    },
    "TypeError": {
        "approach": [
            "Add explicit input validation / type coercion before the failing call.",
            "Add unit tests covering `None` and unexpected types for each parameter.",
        ],
        "risks": [
            "Overly permissive coercion could silently accept invalid input.",
        ],
    },
    "IndexError": {
        "approach": [
            "Add a bounds/length check before indexing.",
            "Add unit tests covering empty sequences and out-of-range indices.",
        ],
        "risks": [
            "A default fallback value may mask an upstream sizing bug.",
        ],
    },
    "AttributeError": {
        "approach": [
            "Add a `None`/type check before attribute access, or use `getattr` with a default.",
            "Add unit tests covering `None` and unexpected object types.",
        ],
        "risks": [
            "Silently defaulting may hide an upstream object-construction bug.",
        ],
    },
}

_DEFAULT_TEMPLATE = {
    "approach": [
        "Add input validation guarding against the observed edge-case input before it reaches the failing call.",
        "Add regression tests that reproduce the exact failure signature observed during reproduction.",
    ],
    "risks": [
        "Root cause is inferred from a single reproduction; verify against additional real-world inputs before shipping.",
    ],
}


def _llm_propose_plan(
    function_name: str,
    module_path: str,
    source: str,
    bug_summary: dict,
    error_type: str,
    repro_confirmed: bool,
    stack_excerpt: list[str],
) -> dict | None:
    if not source:
        return None
    prompt = (
        "You are a senior engineer writing a root-cause analysis and patch plan for a bug.\n\n"
        f"Bug title: {bug_summary.get('title', '')}\n"
        f"Bug description: {bug_summary.get('symptoms', '')}\n"
        f"Failing function: {function_name} in {module_path}\n"
        f"Exception observed: {error_type}\n"
        f"Reproduction confirmed the exception: {repro_confirmed}\n"
        f"Stack trace excerpt: {' | '.join(stack_excerpt) if stack_excerpt else 'n/a'}\n\n"
        "Function source:\n```python\n" + source + "\n```\n\n"
        'Return ONLY JSON of this shape: {"statement": "...", "approach": ["...", "..."], '
        '"risks": ["...", "..."]}. statement is a one-to-two sentence root-cause explanation '
        "grounded in the actual source above. approach is 2-3 concrete patch steps. risks is "
        "1-2 risks of the proposed change. No extra keys, no prose outside the JSON object."
    )
    try:
        result = llm_tools.generate_json(prompt)
    except llm_tools.OllamaUnavailable:
        return None
    statement, approach, risks = result.get("statement"), result.get("approach"), result.get("risks")
    if isinstance(statement, str) and isinstance(approach, list) and isinstance(risks, list) and approach and risks:
        return {"statement": statement, "approach": [str(a) for a in approach], "risks": [str(r) for r in risks]}
    return None


def run(state: WorkflowState) -> None:
    append_trace(state.trace_path, "agent_start", {"agent": "FixPlannerAgent"})
    surface = state.likely_failure_surface
    function_name = surface.get("function", "unknown")
    module_path = surface.get("module", "unknown")
    error_type = state.repro_result.get("failure_signature", "unknown")
    if error_type == "unknown":
        error_type = surface.get("error_type", "unknown")

    matches: list[str] = []
    if function_name != "unknown":
        matches = repo_search(state.repo_root, rf"def {function_name}\b")

    stack_excerpt: list[str] = []
    for block in state.log_evidence:
        if block.get("type") == "stack_trace":
            stack_excerpt = block.get("lines", [])[:3]
            break

    repro_confirmed = bool(state.repro_result.get("failed_consistently"))
    llm_plan = None
    if function_name != "unknown" and state.use_llm and llm_tools.is_available():
        source = read_source_snippet(surface.get("resolved_path", ""))
        llm_plan = _llm_propose_plan(
            function_name, module_path, source, state.bug_summary, error_type, repro_confirmed, stack_excerpt
        )

    if llm_plan:
        statement = llm_plan["statement"]
        approach = llm_plan["approach"]
        risks = llm_plan["risks"]
        plan_source = "llm"
        confidence = 0.9 if repro_confirmed else 0.6
    elif function_name != "unknown":
        statement = (
            f"Failure is likely caused by {function_name}() in {module_path} not handling the "
            f"input that triggered {error_type} during reproduction."
        )
        template = _ERROR_PATCH_TEMPLATES.get(error_type, _DEFAULT_TEMPLATE)
        approach = template["approach"]
        risks = template["risks"]
        plan_source = "rule_based"
        confidence = 0.9 if repro_confirmed else 0.55
    else:
        statement = (
            "Could not resolve a specific function from the logs; root cause is unconfirmed "
            "pending a stack frame that maps to a file in the provided repository."
        )
        template = _DEFAULT_TEMPLATE
        approach = template["approach"]
        risks = template["risks"]
        plan_source = "rule_based"
        confidence = 0.3

    state.root_cause_hypothesis = {
        "statement": statement,
        "confidence": confidence,
        "source": plan_source,
        "supporting_evidence": [
            f"Reproduction result signature: {error_type}",
            (
                f"Repository search for def {function_name}(): {len(matches)} hit(s)"
                if function_name != "unknown"
                else "No function name resolved to search for."
            ),
            f"Stack trace excerpt: {' | '.join(stack_excerpt) if stack_excerpt else 'n/a'}",
        ],
    }

    state.patch_plan = {
        "files_impacted": [module_path] if module_path != "unknown" else [],
        "approach": approach,
        "risks": risks,
        "source": plan_source,
        "repo_search_hits": matches[:5],
    }
    state.validation_plan = {
        "tests_to_add": (
            [
                f"test_{function_name}_{error_type.lower()}_input",
                f"test_{function_name}_regular_values",
            ]
            if function_name != "unknown"
            else ["test_reproduces_failure", "test_regular_values"]
        ),
        "regression_checks": [
            "Run full test suite",
            "Replay recent production payloads for this endpoint",
            f"Check error-rate dashboard for a drop in {error_type}",
        ],
    }
    append_trace(
        state.trace_path,
        "agent_end",
        {"agent": "FixPlannerAgent", "repo_hits": len(matches), "error_type": error_type, "plan_source": plan_source},
    )
