"""Tests for PR body rendering utilities."""
from backend.agents.github.pr_body import render_pr_body, render_step_update


def test_render_pr_body_includes_required_sections() -> None:
    body = render_pr_body(
        run_id="run-123",
        steps_summary=["Implemented feature branch scaffold"],
        validation_summary="All validators passed.",
        metrics={"tests": "0 failed", "lint": "clean"},
    )

    assert "## Summary" in body
    assert "## Changes" in body
    assert "## Validation" in body
    assert "## Metrics" in body
    assert "## Links" in body
    assert "- Run ID: `run-123`" in body
    assert "- Implemented feature branch scaffold" in body
    assert "- tests: 0 failed" in body


def test_render_step_update_lists_acceptance_criteria_and_validators() -> None:
    snippet = render_step_update(
        step_index=1,
        title="Bootstrap integrator",
        acceptance_criteria=["Branch created", "Patch applied"],
        validator_results={
            "ruff": {"status": "passed", "summary": "0 warnings"},
            "mypy": "skipped",
        },
    )

    assert "### Step 1: Bootstrap integrator" in snippet
    assert "- Branch created" in snippet
    assert "- Patch applied" in snippet
    assert "- ruff: passed – 0 warnings" in snippet
    assert "- mypy: skipped" in snippet
