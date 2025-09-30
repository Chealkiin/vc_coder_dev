"""Unit tests covering the orchestrator skeleton."""

from __future__ import annotations

import logging
import sys
from collections import deque
from pathlib import Path
from typing import Deque, Dict, List, Mapping, MutableMapping, Sequence

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.agents.orchestrator.orchestrator_agent import OrchestratorAgent
from backend.agents.orchestrator.orchestrator_state import RunState, StepState
from core.events.publisher import EventsPublisher
from core.events.types import LifecycleEvent
from core.store.repositories import ArtifactRepo, PRBindingRepo, RunRepo, StepRepo, ValidationReportRepo


class InMemoryRunRepo(RunRepo):
    def __init__(self) -> None:
        self.runs: Dict[str, MutableMapping[str, object]] = {}
        self.counter = 0

    def create_run(
        self,
        repo: str,
        base_ref: str,
        steps: Sequence[Mapping[str, object]],
        config: Mapping[str, object] | None = None,
    ) -> str:
        self.counter += 1
        run_id = f"run-{self.counter}"
        self.runs[run_id] = {
            "repo": repo,
            "base_ref": base_ref,
            "state": RunState.QUEUED.value,
        }
        return run_id

    def get_run(self, run_id: str) -> Mapping[str, object] | None:
        return self.runs.get(run_id)

    def update_run_state(self, run_id: str, state: RunState) -> None:
        self.runs[run_id]["state"] = state.value


class InMemoryStepRepo(StepRepo):
    def __init__(self) -> None:
        self.steps: Dict[str, List[MutableMapping[str, object]]] = {}

    def create_steps(self, run_id: str, steps: Sequence[Mapping[str, object]]) -> None:
        self.steps[run_id] = [dict(step) for step in steps]

    def get_step(self, run_id: str, index: int) -> Mapping[str, object] | None:
        try:
            return self.steps[run_id][index]
        except (KeyError, IndexError):
            return None

    def update_step_state(self, run_id: str, index: int, state: StepState) -> None:
        self.steps[run_id][index]["state"] = state.value

    def list_steps(self, run_id: str) -> Sequence[Mapping[str, object]]:
        return list(self.steps.get(run_id, []))


class InMemoryArtifactRepo(ArtifactRepo):
    def record_artifact(self, run_id: str, step_id: str, artifact: Mapping[str, object]) -> None:
        return None


class InMemoryValidationReportRepo(ValidationReportRepo):
    def record_report(self, run_id: str, step_id: str, report: Mapping[str, object]) -> None:
        return None


class InMemoryPRBindingRepo(PRBindingRepo):
    def upsert_binding(self, run_id: str, metadata: Mapping[str, object]) -> None:
        return None


class InMemoryPublisher(EventsPublisher):
    def __init__(self) -> None:
        self.events: Deque[LifecycleEvent] = deque()

    def publish(self, event: LifecycleEvent) -> None:
        self.events.append(event)


def orchestrator(logger: logging.Logger) -> OrchestratorAgent:
    return OrchestratorAgent(
        run_repo=InMemoryRunRepo(),
        step_repo=InMemoryStepRepo(),
        artifact_repo=InMemoryArtifactRepo(),
        validation_report_repo=InMemoryValidationReportRepo(),
        pr_binding_repo=InMemoryPRBindingRepo(),
        events_publisher=InMemoryPublisher(),
        logger=logger,
    )


def test_start_run_initializes_state() -> None:
    logger = logging.getLogger("orch-start")
    logger.handlers = [logging.NullHandler()]
    agent = orchestrator(logger)

    steps = [{"id": "step-1", "state": StepState.QUEUED.value}]
    run_id = agent.start_run("repo/name", "main", steps)

    run_snapshot = agent._run_repo.get_run(run_id)
    assert run_snapshot is not None
    assert run_snapshot["state"] == RunState.RUNNING.value


def test_advance_step_emits_events_and_completes_run() -> None:
    logger = logging.getLogger("orch-advance")
    logger.handlers = [logging.NullHandler()]
    publisher = InMemoryPublisher()
    run_repo = InMemoryRunRepo()
    step_repo = InMemoryStepRepo()

    agent = OrchestratorAgent(
        run_repo=run_repo,
        step_repo=step_repo,
        artifact_repo=InMemoryArtifactRepo(),
        validation_report_repo=InMemoryValidationReportRepo(),
        pr_binding_repo=InMemoryPRBindingRepo(),
        events_publisher=publisher,
        logger=logger,
    )

    steps = [{"id": "step-1", "state": StepState.QUEUED.value}]
    run_id = agent.start_run("repo/name", "main", steps)

    observed_states = []
    for _ in range(6):
        observed_states.append(agent.advance_step(run_id))

    assert observed_states[-1] == StepState.MERGED
    assert run_repo.get_run(run_id)["state"] == RunState.COMPLETED.value
    assert any(event.state == StepState.MERGED.value for event in publisher.events)

