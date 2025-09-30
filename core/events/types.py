"""Event type definitions for the agent orchestration system."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping


class LifecycleEventType(str, Enum):
    """Enumeration of the canonical event categories."""

    STEP_PLANNED = "step.planned"
    STEP_EXECUTING = "step.executing"
    STEP_VALIDATED = "step.validated"
    STEP_COMMITTED = "step.committed"
    STEP_PAUSED = "step.paused"
    STEP_FAILED = "step.failed"
    RUN_STATUS_CHANGED = "run.status_changed"


@dataclass(frozen=True)
class LifecycleEvent:
    """Base payload emitted by the orchestrator when lifecycle milestones occur."""

    run_id: str
    state: str
    timestamp: datetime
    event_type: LifecycleEventType
    step_id: str | None = None
    duration_ms: int | None = None
    meta: Mapping[str, object] | None = None

    @property
    def type(self) -> LifecycleEventType:
        """Expose the canonical event type."""

        return self.event_type

    def to_dict(self) -> Mapping[str, object]:
        """Return a serialisable mapping representation."""

        payload: dict[str, object] = {
            "run_id": self.run_id,
            "step_id": self.step_id,
            "state": self.state,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
        }
        if self.duration_ms is not None:
            payload["duration_ms"] = self.duration_ms
        if self.meta is not None:
            payload["meta"] = dict(self.meta)
        return payload


@dataclass(frozen=True)
class StepPlanned(LifecycleEvent):
    """Event emitted when the orchestrator plans a step."""

    event_type: LifecycleEventType = LifecycleEventType.STEP_PLANNED


@dataclass(frozen=True)
class StepExecuting(LifecycleEvent):
    """Event emitted when the orchestrator marks a step as executing."""

    event_type: LifecycleEventType = LifecycleEventType.STEP_EXECUTING


@dataclass(frozen=True)
class StepValidated(LifecycleEvent):
    """Event emitted when the orchestrator validates a step outcome."""

    event_type: LifecycleEventType = LifecycleEventType.STEP_VALIDATED


@dataclass(frozen=True)
class StepCommitted(LifecycleEvent):
    """Event emitted when the orchestrator commits a step result."""

    event_type: LifecycleEventType = LifecycleEventType.STEP_COMMITTED


@dataclass(frozen=True)
class StepPaused(LifecycleEvent):
    """Event emitted when the orchestrator pauses a step."""

    event_type: LifecycleEventType = LifecycleEventType.STEP_PAUSED


@dataclass(frozen=True)
class StepFailed(LifecycleEvent):
    """Event emitted when the orchestrator marks a step as failed."""

    event_type: LifecycleEventType = LifecycleEventType.STEP_FAILED


@dataclass(frozen=True)
class RunStatusChanged(LifecycleEvent):
    """Event emitted when the overall run state changes."""

    event_type: LifecycleEventType = LifecycleEventType.RUN_STATUS_CHANGED
