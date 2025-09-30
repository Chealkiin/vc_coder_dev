"""Tests for coder prompt builders and diff utilities."""

from __future__ import annotations

from uuid import uuid4

from backend.agents.coder import diff_utils
from backend.agents.coder.coder_adapter import BaseCoderAdapter
from backend.agents.coder.prompt_templates import build_coder_prompt
from core.contracts.work_order import WorkOrder


class DummyCoder(BaseCoderAdapter):
    pass


def _make_work_order() -> WorkOrder:
    return WorkOrder(
        work_order_id=uuid4(),
        title="Add login",
        objective="Implement POST /login",
        constraints=["Focus on auth handler", "Do not add or modify dependencies."],
        acceptance_criteria=["Users receive JWT", "Tests pass"],
        context_files=["backend/api/auth.py"],
        dependencies=[],
        return_format="unified-diff",
    )


def test_coder_prompt_contains_constraints_and_criteria() -> None:
    work_order = _make_work_order()
    prompt_one = build_coder_prompt(work_order)
    prompt_two = DummyCoder().build_coder_prompt(work_order)
    assert prompt_one == prompt_two
    assert "Focus on auth handler" in prompt_one
    assert "Users receive JWT" in prompt_one
    assert "diff --git" in prompt_one
    assert "Return exactly the diff" in prompt_one


def test_is_unified_diff_and_summary() -> None:
    diff_text = """diff --git a/backend/api/auth.py b/backend/api/auth.py\nindex 123..456 100644\n--- a/backend/api/auth.py\n+++ b/backend/api/auth.py\n@@ -1,3 +1,4 @@\n-import old\n+import new\n+added_line\n return True\n"""
    assert diff_utils.is_unified_diff(diff_text)
    summary = diff_utils.summarize_unified_diff(diff_text)
    assert summary == {"changed_files": 1, "additions": 2, "deletions": 1}


def test_find_new_files_detects_created_paths() -> None:
    diff_text = """diff --git a/dev/null b/docs/new.md\nnew file mode 100644\nindex 0000000..1111111\n--- /dev/null\n+++ b/docs/new.md\n@@ -0,0 +1,2 @@\n+hello\n+world\n"""
    assert diff_utils.is_unified_diff(diff_text)
    new_files = diff_utils.find_new_files(diff_text)
    assert new_files == ["docs/new.md"]


def test_is_unified_diff_rejects_plain_text() -> None:
    assert not diff_utils.is_unified_diff("print('hello world')")
