"""State definitions used by the orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Mapping


class StepState(str, Enum):
    """Lifecycle states for an individual step."""

    QUEUED = "queued"
    PLANNED = "planned"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMMITTING = "committing"
    PR_UPDATED = "pr_updated"
    MERGED = "merged"
    PAUSED = "paused"
    FAILED = "failed"


class RunState(str, Enum):
    """Lifecycle states for the overall run."""

    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class StepSnapshot:
    """Snapshot describing the persisted state of a step."""

    run_id: str
    index: int
    name: str
    state: StepState
    created_at: datetime
    updated_at: datetime
    meta: Mapping[str, object] = field(default_factory=dict)


@dataclass
class RunSnapshot:
    """Snapshot describing the persisted state of a run."""

    run_id: str
    repository: str
    base_ref: str
    state: RunState
    created_at: datetime
    updated_at: datetime
    current_step_index: int | None = None
    total_steps: int | None = None
    meta: Mapping[str, object] = field(default_factory=dict)

