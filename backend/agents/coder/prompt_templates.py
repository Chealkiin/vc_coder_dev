"""Deterministic prompt builders for the coder agent."""

from __future__ import annotations

from typing import Mapping, Sequence

from core.contracts.work_order import WorkOrder


def _ensure_sequence(values: Sequence[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                normalized.append(stripped)
    return normalized


def _format_list(items: Sequence[str], prefix: str) -> list[str]:
    return [f"{prefix}{item}" for item in items]


def build_coder_prompt(
    work_order: WorkOrder,
    repo_meta: Mapping[str, object] | None = None,
) -> str:
    """Return the deterministic prompt for GPT-5-Codex."""

    constraints = _ensure_sequence(work_order.constraints)
    criteria = _ensure_sequence(work_order.acceptance_criteria)
    context_files = _ensure_sequence(work_order.context_files)

    repo_details: list[str] = []
    if repo_meta:
        if (name := repo_meta.get("name")):
            repo_details.append(f"Repository: {name}")
        if (default_branch := repo_meta.get("default_branch")):
            repo_details.append(f"Default branch: {default_branch}")
        if (languages := repo_meta.get("languages")):
            repo_details.append(f"Primary languages: {languages}")

    lines: list[str] = []
    lines.append("You are GPT-5-Codex operating as an autonomous code editor.")
    lines.append("Follow the work order exactly and keep the diff minimal and reviewable.")
    lines.append("")
    lines.append(f"Work Order: {work_order.title}")
    lines.append(f"Objective: {work_order.objective}")

    if repo_details:
        lines.append("Repository Context:")
        lines.extend(_format_list(repo_details, "  - "))

    if context_files:
        lines.append("Allowed files to modify (repo-relative):")
        lines.extend(_format_list(context_files, "  - "))
    else:
        lines.append("No context files provided; inspect only files you explicitly touch.")

    if constraints:
        lines.append("Constraints (must obey):")
        lines.extend(_format_list(constraints, "  - "))
    else:
        lines.append("Constraints: none beyond standard coding best practices.")

    if criteria:
        lines.append("Acceptance criteria to satisfy:")
        lines.extend(_format_list(criteria, "  - "))

    lines.append("")
    lines.append("Diff Requirements:")
    lines.append("  - Output ONLY a single `diff --git` unified diff.")
    lines.append(
        "  - Do not include explanations, notes, tests run, or any text outside the diff."
    )
    lines.append("  - Paths in the diff must be relative to the repository root.")
    lines.append("  - Keep changes narrowly scoped and minimal.")
    lines.append(
        "  - Unless a constraint explicitly allows it, do NOT add new dependencies or"
        " modify dependency manifests/lockfiles."
    )
    lines.append("  - Do not generate non-deterministic values (timestamps, UUIDs, hashes).")
    lines.append(
        "  - Ensure the diff applies cleanly with `git apply` and uses UTF-8 text."
    )

    lines.append("")
    lines.append("Return exactly the diff. No surrounding markdown fences.")

    return "\n".join(lines)
