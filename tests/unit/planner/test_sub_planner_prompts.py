"""Tests for the sub-planner prompt builders and adapter."""

from __future__ import annotations

from uuid import uuid4

from backend.agents.planner.prompt_templates import (
    build_planner_summary,
    build_work_order_brief,
)
from backend.agents.planner.sub_planner_adapter import BasicSubPlanner


def _make_step() -> dict[str, object]:
    work_order_id = uuid4()
    return {
        "work_order_id": work_order_id,
        "title": "  Implement login endpoint  ",
        "objective": "  Create POST /login handler ",
        "constraints": [" Focus only on auth module"],
        "acceptance_criteria": (" Users can authenticate", " Response includes token "),
        "context_files": ["backend/api/auth.py", " README.md  "],
    }


def test_planner_templates_are_deterministic() -> None:
    step = _make_step()
    first = build_planner_summary(step)
    second = build_planner_summary(step)
    assert first == second


def test_work_order_brief_is_deterministic() -> None:
    planner = BasicSubPlanner()
    work_order = planner.build_work_order(_make_step())
    brief_one = build_work_order_brief(work_order.to_dict())
    brief_two = build_work_order_brief(work_order.to_dict())
    assert brief_one == brief_two


def test_basic_sub_planner_normalizes_fields() -> None:
    planner = BasicSubPlanner()
    step = _make_step()
    work_order = planner.build_work_order(step)

    assert work_order.title == "Implement login endpoint"
    assert work_order.objective == "Create POST /login handler"
    assert planner.DEFAULT_DEPENDENCY_CONSTRAINT in work_order.constraints
    assert work_order.return_format == "unified-diff"
    assert work_order.dependencies == []
    assert work_order.context_files[0] == "backend/api/auth.py"
    assert work_order.context_files[1] == "README.md"
    assert "Normalized title whitespace" in planner.transform_log
    assert "Generated work order brief" in "\n".join(planner.transform_log)


def test_basic_sub_planner_defaults_context_allowlist_when_missing() -> None:
    planner = BasicSubPlanner()
    step = {
        "work_order_id": uuid4(),
        "title": "Add search",
        "objective": "Implement search endpoint",
    }
    work_order = planner.build_work_order(step)
    assert work_order.context_files == list(planner.DEFAULT_CONTEXT_ALLOWLIST)
