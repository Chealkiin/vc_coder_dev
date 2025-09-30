"""Run orchestrator state machine stubs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Protocol

from backend.core.contracts.work_order import WorkOrder
from backend.core.events.lifecycle import LifecycleEvent, LifecycleEventType
from backend.core.logging import get_logger
from backend.core.models.step import Step
from backend.core.models.validation import ValidationReport

logger = get_logger(__name__)


class OrchestratorState(str, Enum):
    """Enumeration of orchestrator states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Planner(Protocol):
    """Planner interface for initial planning."""

    def plan(self, step: Step) -> WorkOrder:
        """Generate a work order from the provided step."""


class SubPlanner(Protocol):
    """Sub-planner interface for detailed planning."""

    def plan(self, step: Step) -> WorkOrder:
        """Generate a detailed work order from the provided step."""


class Coder(Protocol):
    """Coder adapter interface."""

    def execute(self, work_order: WorkOrder) -> str:
        """Execute the work order and return a unified diff."""


class Validator(Protocol):
    """Validator interface."""

    def validate(self, changed_paths: Iterable[str]) -> ValidationReport:
        """Validate the changed paths and produce a report."""


class EventPublisher(Protocol):
    """Lifecycle event publication interface."""

    def publish(self, event: LifecycleEvent) -> None:
        """Publish a lifecycle event."""


@dataclass
class Orchestrator:
    """Sequential orchestrator coordinating planner, coder, and validator."""

    planner: Planner
    sub_planner: SubPlanner
    coder: Coder
    validator: Validator
    event_publisher: EventPublisher
    state: OrchestratorState = OrchestratorState.IDLE

    def run(self, steps: Iterable[Step]) -> None:
        """Execute the orchestrator workflow for provided steps.

        Args:
            steps: An iterable of run steps to process sequentially.

        Note:
            # TODO(team, 2024-05-22): Implement full orchestration loop with persistence hooks.
        """

        self.state = OrchestratorState.RUNNING
        for step in steps:
            self._publish(LifecycleEventType.STEP_PLANNED, step)
            work_order = self.sub_planner.plan(step)
            diff = self.coder.execute(work_order)
            self.validator.validate(self._extract_changed_paths(diff))
            self._publish(LifecycleEventType.STEP_VALIDATED, step)
        self.state = OrchestratorState.COMPLETED
        logger.info("orchestrator.completed", extra={"meta": {"state": self.state}})

    def _publish(self, event_type: LifecycleEventType, step: Step) -> None:
        """Publish a lifecycle event for the given step."""

        event = LifecycleEvent(
            event_type=event_type,
            run_id=step.run_id,
            step_id=step.id,
            occurred_at=step.updated_at,
            payload={"status": step.status},
        )
        self.event_publisher.publish(event)

    def _extract_changed_paths(self, diff: str) -> Iterable[str]:
        """Extract changed file paths from a unified diff."""

        # TODO(team, 2024-05-22): Implement diff parsing once coder output is finalized.
        return []
