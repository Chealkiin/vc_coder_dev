"""Deterministic prompt templates for planner + sub-planner agents."""

from __future__ import annotations

from typing import Iterable, Mapping


def _coerce_iterable_strings(values: object) -> list[str]:
    """Return a list of string values preserving input order."""

    items: list[str] = []
    if values is None:
        return items
    if isinstance(values, str):
        candidate = values.strip()
        if candidate:
            items.append(candidate)
        return items
    if isinstance(values, Iterable):
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                items.append(text)
    return items


def build_planner_summary(step: Mapping[str, object]) -> str:
    """Return a condensed summary of the normalized planning step."""

    title = str(step.get("title", ""))
    objective = str(step.get("objective", step.get("description", "")))
    constraints = _coerce_iterable_strings(step.get("constraints"))
    criteria = _coerce_iterable_strings(step.get("acceptance_criteria"))
    context_files = _coerce_iterable_strings(step.get("context_files"))

    lines: list[str] = []
    lines.append("[Planner Step Summary]")
    lines.append(f"Title: {title.strip() or 'Untitled'}")
    lines.append(f"Objective: {objective.strip() or 'None provided'}")

    if constraints:
        lines.append("Constraints:")
        for idx, constraint in enumerate(constraints, start=1):
            lines.append(f"  {idx}. {constraint}")
    else:
        lines.append("Constraints: none specified")

    if criteria:
        lines.append("Acceptance Criteria:")
        for idx, criterion in enumerate(criteria, start=1):
            lines.append(f"  {idx}. {criterion}")
    else:
        lines.append("Acceptance Criteria: none provided")

    if context_files:
        lines.append("Context Files:")
        for path in context_files:
            lines.append(f"  - {path}")

    return "\n".join(lines)


def build_work_order_brief(work_order: Mapping[str, object]) -> str:
    """Return a deterministic human readable work order summary."""

    constraints = _coerce_iterable_strings(work_order.get("constraints"))
    criteria = _coerce_iterable_strings(work_order.get("acceptance_criteria"))
    context_files = _coerce_iterable_strings(work_order.get("context_files"))

    lines: list[str] = []
    lines.append("[Work Order Brief]")
    lines.append(f"Title: {work_order.get('title', '')}")
    lines.append(f"Objective: {work_order.get('objective', '')}")
    lines.append(f"Return Format: {work_order.get('return_format', '')}")

    lines.append("Constraints:")
    if constraints:
        for idx, constraint in enumerate(constraints, start=1):
            lines.append(f"  {idx}. {constraint}")
    else:
        lines.append("  (none)")

    lines.append("Acceptance Criteria:")
    if criteria:
        for idx, criterion in enumerate(criteria, start=1):
            lines.append(f"  {idx}. {criterion}")
    else:
        lines.append("  (none)")

    lines.append("Context Files:")
    if context_files:
        for path in context_files:
            lines.append(f"  - {path}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)
