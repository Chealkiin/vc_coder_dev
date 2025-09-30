"""Integration-focused unit tests for orchestrator dependency wiring."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Mapping, MutableMapping, Sequence
from uuid import uuid4

import pytest

from backend.agents.orchestrator.orchestrator_agent import OrchestratorAgent
from backend.agents.orchestrator.orchestrator_state import RunState, StepState
from backend.agents.orchestrator.routing import (
    CoderAdapter,
    GitHubClient,
    PlannerAdapter,
    SubPlannerAdapter,
    ValidatorService,
)
from core.events.publisher import EventsPublisher
from core.events.types import LifecycleEvent, RunStatusChanged, StepCommitted, StepExecuting, StepPlanned, StepValidated
from core.store.repositories import ArtifactRepo, PRBindingRepo, RunRepo, StepRepo, ValidationReportRepo


@dataclass
class FakeWorkOrder:
    work_order_id: str
    title: str
    objective: str
    constraints: list[str]
    acceptance_criteria: list[str]
    context_files: list[str]
    dependencies: list[str]
    return_format: str

    def to_dict(self) -> Mapping[str, object]:
        return {
            "work_order_id": self.work_order_id,
            "title": self.title,
            "objective": self.objective,
            "constraints": list(self.constraints),
            "acceptance_criteria": list(self.acceptance_criteria),
            "context_files": list(self.context_files),
            "dependencies": list(self.dependencies),
            "return_format": self.return_format,
        }


@dataclass
class FakeCoderResult:
    work_order_id: str
    diff: str
    notes: str | None

    def to_dict(self) -> Mapping[str, object]:
        return {
            "work_order_id": self.work_order_id,
            "diff": self.diff,
            "notes": self.notes,
        }


@dataclass
class FakeValidationReport:
    step_id: str
    fatal: list[object]
    warnings: list[object]
    metrics: Mapping[str, object]

    def to_dict(self) -> Mapping[str, object]:
        return {
            "step_id": self.step_id,
            "fatal": list(self.fatal),
            "warnings": list(self.warnings),
            "metrics": dict(self.metrics),
        }


class RunRepoFake(RunRepo):
    def __init__(self) -> None:
        self.runs: MutableMapping[str, MutableMapping[str, object]] = {}
        self._counter = 0

    def create_run(
        self,
        *,
        repo: str,
        base_ref: str,
        feature_ref: str,
        status: RunState,
        config: Mapping[str, object] | None = None,
    ) -> str:
        run_id = f"run-{self._counter}"
        self._counter += 1
        self.runs[run_id] = {
            "id": run_id,
            "repo": repo,
            "base_ref": base_ref,
            "feature_ref": feature_ref,
            "state": status,
            "config": dict(config or {}),
        }
        return run_id

    def get_run(self, run_id: str) -> Mapping[str, object] | None:
        return self.runs.get(run_id)

    def update_run_state(self, run_id: str, state: RunState) -> None:
        self.runs[run_id]["state"] = state


class StepRepoFake(StepRepo):
    def __init__(self) -> None:
        self.steps: MutableMapping[str, List[MutableMapping[str, object]]] = {}

    def create_steps(
        self, run_id: str, steps: Sequence[Mapping[str, object]]
    ) -> Sequence[Mapping[str, object]]:
        stored: List[MutableMapping[str, object]] = [dict(step) for step in steps]
        self.steps[run_id] = stored
        return stored

    def list_steps(self, run_id: str) -> Sequence[Mapping[str, object]]:
        return [dict(step) for step in self.steps.get(run_id, [])]

    def update_step_state(self, run_id: str, step_id: str, state: StepState) -> None:
        for step in self.steps.get(run_id, []):
            if str(step["id"]) == step_id:
                step["state"] = state.value
                break

    def update_step_metadata(
        self,
        run_id: str,
        step_id: str,
        *,
        plan: Mapping[str, object] | None = None,
        work_order: Mapping[str, object] | None = None,
        coder_result: Mapping[str, object] | None = None,
    ) -> None:
        for step in self.steps.get(run_id, []):
            if str(step["id"]) != step_id:
                continue
            if plan is not None:
                step["plan"] = dict(plan)
            if work_order is not None:
                step["work_order"] = dict(work_order)
            if coder_result is not None:
                step["coder_result"] = dict(coder_result)
            break


class ArtifactRepoFake(ArtifactRepo):
    def __init__(self) -> None:
        self.artifacts: list[Mapping[str, object]] = []

    def add(
        self,
        *,
        run_id: str,
        step_id: str,
        kind: str,
        content: str,
        meta: Mapping[str, object] | None = None,
    ) -> None:
        self.artifacts.append(
            {
                "run_id": run_id,
                "step_id": step_id,
                "kind": kind,
                "content": content,
                "meta": dict(meta or {}),
            }
        )


class ValidationReportRepoFake(ValidationReportRepo):
    def __init__(self) -> None:
        self.reports: list[Mapping[str, object]] = []

    def add(
        self,
        *,
        run_id: str,
        step_id: str,
        report: Mapping[str, object],
    ) -> None:
        self.reports.append({"run_id": run_id, "step_id": step_id, "report": dict(report)})


class PRRepoFake(PRBindingRepo):
    def __init__(self) -> None:
        self.binding: Mapping[str, object] | None = None

    def get(self, run_id: str) -> Mapping[str, object] | None:  # pragma: no cover - simple getter
        return self.binding

    def upsert(self, run_id: str, metadata: Mapping[str, object]) -> None:
        self.binding = dict(metadata)


class PlannerFake(PlannerAdapter):
    def plan_step(self, step: Mapping[str, object]) -> Mapping[str, object]:
        return dict(step)


class SubPlannerFake(SubPlannerAdapter):
    def build_work_order(self, step: Mapping[str, object]) -> FakeWorkOrder:
        return FakeWorkOrder(
            work_order_id=str(uuid4()),
            title=str(step.get("title", "")),
            objective=str(step.get("body", "")),
            constraints=["return unified diff"],
            acceptance_criteria=[],
            context_files=[],
            dependencies=[],
            return_format="unified-diff",
        )


class CoderFake(CoderAdapter):
    def execute(self, work_order: FakeWorkOrder) -> FakeCoderResult:
        diff = "\n".join(
            [
                "diff --git a/file.txt b/file.txt",
                "--- a/file.txt",
                "+++ b/file.txt",
                "@@",
                "+hello",
            ]
        )
        return FakeCoderResult(work_order_id=work_order.work_order_id, diff=diff, notes="did work")


class ValidatorFake(ValidatorService):
    def validate(self, diff: str, base_ref: str, feature_ref: str) -> FakeValidationReport:
        return FakeValidationReport(step_id=str(uuid4()), fatal=[], warnings=[], metrics={})


class GitHubClientFake(GitHubClient):
    def __init__(self) -> None:
        self.ensure_calls: list[tuple[str, str]] = []
        self.patch_calls: list[tuple[str, str]] = []
        self.pr_calls: list[tuple[str, str, str, str]] = []
        self.update_calls: list[tuple[int, str]] = []

    def ensure_branch(self, base_ref: str, feature_ref: str) -> None:
        self.ensure_calls.append((base_ref, feature_ref))

    def apply_patch(self, feature_ref: str, unified_diff: str) -> Mapping[str, object]:
        self.patch_calls.append((feature_ref, unified_diff))
        return {"changed_files": 1, "additions": 1, "deletions": 0}

    def create_or_update_pr(self, title: str, body_md: str, head: str, base: str) -> tuple[int, str]:
        self.pr_calls.append((title, body_md, head, base))
        return 7, "https://example.invalid/pull/7"

    def update_pr_body(self, pr_number: int, body_md: str) -> None:
        self.update_calls.append((pr_number, body_md))


class EventsPublisherFake(EventsPublisher):
    def __init__(self) -> None:
        self.events: list[LifecycleEvent] = []

    def publish(self, event: LifecycleEvent) -> None:
        self.events.append(event)


@pytest.fixture
def orchestrator_components() -> Mapping[str, object]:
    run_repo = RunRepoFake()
    step_repo = StepRepoFake()
    artifact_repo = ArtifactRepoFake()
    report_repo = ValidationReportRepoFake()
    pr_repo = PRRepoFake()
    planner = PlannerFake()
    sub_planner = SubPlannerFake()
    coder = CoderFake()
    validator = ValidatorFake()
    github = GitHubClientFake()
    events = EventsPublisherFake()
    config = {"feature_branch": "feat/test", "merge": {"auto": False}}
    logger = logging.getLogger("tests.orchestrator")

    agent = OrchestratorAgent(
        run_repo=run_repo,
        step_repo=step_repo,
        artifact_repo=artifact_repo,
        report_repo=report_repo,
        pr_repo=pr_repo,
        planner_adapter=planner,
        sub_planner_adapter=sub_planner,
        coder_adapter=coder,
        validator_service=validator,
        github_client=github,
        events=events,
        logger=logger,
        config=config,
    )

    return {
        "agent": agent,
        "run_repo": run_repo,
        "step_repo": step_repo,
        "artifact_repo": artifact_repo,
        "report_repo": report_repo,
        "pr_repo": pr_repo,
        "github": github,
        "events": events,
    }


def test_orchestrator_advances_step(orchestrator_components: Mapping[str, object]) -> None:
    agent: OrchestratorAgent = orchestrator_components["agent"]  # type: ignore[assignment]
    run_repo: RunRepoFake = orchestrator_components["run_repo"]  # type: ignore[assignment]
    step_repo: StepRepoFake = orchestrator_components["step_repo"]  # type: ignore[assignment]
    artifact_repo: ArtifactRepoFake = orchestrator_components["artifact_repo"]  # type: ignore[assignment]
    report_repo: ValidationReportRepoFake = orchestrator_components["report_repo"]  # type: ignore[assignment]
    pr_repo: PRRepoFake = orchestrator_components["pr_repo"]  # type: ignore[assignment]
    github: GitHubClientFake = orchestrator_components["github"]  # type: ignore[assignment]
    events: EventsPublisherFake = orchestrator_components["events"]  # type: ignore[assignment]

    run_id = agent.start_run(
        "octo/repo",
        "main",
        steps=[{"id": "step-1", "title": "Add feature", "body": "Implement feature"}],
    )

    final_state = agent.advance_step(run_id)

    assert final_state == StepState.PR_UPDATED
    assert run_repo.runs[run_id]["state"] == RunState.COMPLETED

    stored_step = step_repo.steps[run_id][0]
    assert stored_step["state"] in {StepState.PR_UPDATED.value, StepState.MERGED.value}
    assert "work_order" in stored_step
    assert "coder_result" in stored_step

    kinds = {artifact["kind"] for artifact in artifact_repo.artifacts}
    assert kinds == {"diff", "doc"}

    assert len(report_repo.reports) == 1
    assert pr_repo.binding is not None
    assert github.ensure_calls
    assert github.pr_calls

    event_types = [type(event) for event in events.events]
    assert event_types.count(RunStatusChanged) == 2
    assert any(isinstance(event, StepPlanned) for event in events.events)
    assert any(isinstance(event, StepExecuting) for event in events.events)
    assert any(isinstance(event, StepValidated) for event in events.events)
    committed_events = [event for event in events.events if isinstance(event, StepCommitted)]
    assert len(committed_events) >= 1
