"""Integration test covering the happy-path demo wiring."""

from __future__ import annotations

from backend.agents.orchestrator.orchestrator_state import StepState
from backend.agents.orchestrator.wiring_demo import build_demo_orchestrator
from scripts.demo_happy_path import DEMO_STEPS


def test_demo_happy_path_executes_full_lifecycle(monkeypatch) -> None:
    """Ensure the orchestrator with fakes runs both steps without pausing."""

    monkeypatch.setenv("SIZE_GUARDS_ENABLED", "false")
    context = build_demo_orchestrator()
    run_id = context.orchestrator.start_run(
        repo="org/demo-repo", base_ref="main", steps=list(DEMO_STEPS)
    )

    terminal_states = {StepState.PR_UPDATED.value, StepState.MERGED.value}
    while True:
        step_records = context.step_repo.list_steps(run_id)
        if all(record.get("state") in terminal_states for record in step_records):
            break
        context.orchestrator.advance_step(run_id)

    step_states = {record["id"]: record["state"] for record in context.step_repo.list_steps(run_id)}
    assert step_states
    assert all(state in terminal_states for state in step_states.values())

    events = context.events.list_events(run_id)
    event_types = [event.event_type.value for event in events]
    assert event_types[:1] == ["run.status_changed"]
    assert event_types.count("step.planned") == 2
    assert event_types.count("step.executing") == 2
    assert event_types.count("step.validated") == 2
    committed_events = [event for event in events if event.event_type.value == "step.committed"]
    assert len(committed_events) >= 4
    assert event_types[-1] == "run.status_changed"

    artifacts = context.artifact_repo.all_artifacts()
    diff_artifacts = [artifact for artifact in artifacts if artifact["kind"] == "diff"]
    assert diff_artifacts, "expected diff artifact to be persisted"

    reports = context.report_repo.list_reports(run_id)
    assert reports
    assert all(report["fatal_count"] == 0 for report in reports)
