"""Factory helpers that wire the orchestrator with in-memory fakes for demos."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping

from backend.agents.coder.coder_adapter_fake import CoderAdapterFake
from backend.agents.github.github_client_fake import GitHubClientFake
from backend.agents.orchestrator.orchestrator_agent import OrchestratorAgent
from backend.agents.planner.sub_planner_adapter_fake import SubPlannerAdapterFake
from backend.agents.validator.fake_validator import FakeValidator
from core.events.capture import InMemoryEventsPublisher
from core.store.memory_repos import (
    InMemoryArtifactRepo,
    InMemoryPRBindingRepo,
    InMemoryRunRepo,
    InMemoryStepRepo,
    InMemoryValidationReportRepo,
)


@dataclass(slots=True)
class DemoOrchestratorContext:
    """Container returned by :func:`build_demo_orchestrator`."""

    orchestrator: OrchestratorAgent
    run_repo: InMemoryRunRepo
    step_repo: InMemoryStepRepo
    artifact_repo: InMemoryArtifactRepo
    report_repo: InMemoryValidationReportRepo
    pr_repo: InMemoryPRBindingRepo
    events: InMemoryEventsPublisher


class PlannerPassthrough:
    """Minimal planner adapter that echoes step metadata.

    The production orchestrator expects a planner adapter, but the happy
    path demo focuses on exercising the sub-planner → coder → validator
    pipeline. This passthrough preserves input structure so the fake
    sub-planner can normalise the payload deterministically.
    """

    def plan_step(self, step: Mapping[str, object]) -> Mapping[str, object]:
        """Return a shallow copy of ``step`` to satisfy the protocol."""

        return dict(step)


def build_demo_orchestrator(*, config: Mapping[str, object] | None = None) -> DemoOrchestratorContext:
    """Return an :class:`OrchestratorAgent` wired against in-memory fakes."""

    run_repo = InMemoryRunRepo()
    step_repo = InMemoryStepRepo()
    artifact_repo = InMemoryArtifactRepo()
    report_repo = InMemoryValidationReportRepo()
    pr_repo = InMemoryPRBindingRepo()
    events = InMemoryEventsPublisher()

    planner = PlannerPassthrough()
    sub_planner = SubPlannerAdapterFake()
    coder = CoderAdapterFake()
    validator = FakeValidator()
    github = GitHubClientFake()

    logger = logging.getLogger("demo.orchestrator")

    orchestrator = OrchestratorAgent(
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
        config=config or {"feature_branch": "demo/happy-path"},
    )

    return DemoOrchestratorContext(
        orchestrator=orchestrator,
        run_repo=run_repo,
        step_repo=step_repo,
        artifact_repo=artifact_repo,
        report_repo=report_repo,
        pr_repo=pr_repo,
        events=events,
    )


__all__ = ["DemoOrchestratorContext", "build_demo_orchestrator"]
