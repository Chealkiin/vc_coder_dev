"""Run the happy-path orchestrator demo using in-memory fakes."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from backend.agents.orchestrator.orchestrator_state import StepState
from backend.agents.orchestrator.wiring_demo import DemoOrchestratorContext, build_demo_orchestrator

DEMO_STEPS: Sequence[dict[str, object]] = (
    {
        "title": "Add Settings route scaffold",
        "body": "Create placeholder Settings page in the frontend app",
    },
    {
        "title": "Add placeholder tests for Settings route",
        "body": "Outline tests ensuring the Settings page renders",
    },
)


def main() -> int:
    """Execute the end-to-end happy-path demo."""

    os.environ.setdefault("SIZE_GUARDS_ENABLED", "false")
    context = build_demo_orchestrator()
    orchestrator = context.orchestrator

    run_id = orchestrator.start_run(repo="org/demo-repo", base_ref="main", steps=list(DEMO_STEPS))

    _drain_steps(context, run_id)
    _print_event_summary(context, run_id)
    _print_artifact_summary(context, run_id)

    return 0


def _drain_steps(context: DemoOrchestratorContext, run_id: str) -> None:
    """Advance steps sequentially until the run reaches a terminal state."""

    while True:
        step_records = context.step_repo.list_steps(run_id)
        pending = [record for record in step_records if record.get("state") not in {StepState.PR_UPDATED.value, StepState.MERGED.value}]
        if not pending:
            break
        orchestrator = context.orchestrator
        orchestrator.advance_step(run_id)


def _print_event_summary(context: DemoOrchestratorContext, run_id: str) -> None:
    """Print the lifecycle events emitted during the run."""

    for event in context.events.list_events(run_id):
        step_id = event.step_id or "-"
        print(
            f"{event.timestamp.isoformat()} run={event.run_id} step={step_id} "
            f"state={event.state} event={event.event_type.value}"
        )


def _print_artifact_summary(context: DemoOrchestratorContext, run_id: str) -> None:
    """Print a short artifact summary to highlight diff persistence."""

    for step in context.step_repo.list_steps(run_id):
        artifacts = context.artifact_repo.list_artifacts(str(step["id"]))
        print(f"Artifacts for {step['id']}: {[artifact['kind'] for artifact in artifacts]}")


if __name__ == "__main__":
    raise SystemExit(main())
