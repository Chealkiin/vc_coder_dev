"""Mapping tables between step types and output contracts."""

from __future__ import annotations

STEP_TO_OUTPUT = {
    "code_generation": "file_patch",
    "code_refactor": "file_patch",
    "code_fix": "file_patch",
    "test_generation": "file_patch",
    "file_patch": "file_patch",
    "code_review": "quality_result",
    "style_check": "quality_result",
    "format_fix": "quality_result",
    "validate_code": "quality_result",
    "generate_plan": "plan_result",
    "validate_plan": "plan_result",
    "execute_plan": "orchestrator_result",
    "orchestrate_step": "orchestrator_result",
    "memory_lookup": "context",
    "context_fetch": "context",
    "symbol_lookup": "context",
}

ALIASES = {
    "gen_code": "code_generation",
    "refactor_code": "code_refactor",
    "fix_code": "code_fix",
    "gen_tests": "test_generation",
    "review_code": "code_review",
    "lint": "style_check",
    "format_code": "format_fix",
    "plan": "generate_plan",
    "plan_validate": "validate_plan",
    "execute": "execute_plan",
    "orchestrate": "orchestrate_step",
    "lookup_memory": "memory_lookup",
    "fetch_context": "context_fetch",
    "lookup_symbol": "symbol_lookup",
}


def normalize_step_type(step_type: str) -> str:
    """Return the canonical step type for the provided identifier."""

    canonical = ALIASES.get(step_type, step_type)
    return canonical

