"""Event definitions for run and step lifecycle transitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class LifecycleEventType(str, Enum):
    """Enumeration of orchestrator lifecycle event types."""

    RUN_CREATED = "run.created"
    RUN_COMPLETED = "run.completed"
    STEP_PLANNED = "step.planned"
    STEP_EXECUTING = "step.executing"
    STEP_VALIDATED = "step.validated"
    STEP_FAILED = "step.failed"
    STEP_COMMITTED = "step.committed"
    STEP_MERGED = "step.merged"


@dataclass(frozen=True)
class LifecycleEvent:
    """Represents a structured lifecycle event payload."""

    event_type: LifecycleEventType
    run_id: str
    step_id: Optional[str]
    occurred_at: datetime
    payload: Dict[str, str]
