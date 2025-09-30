"""State machine helpers for orchestrator step progression."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable

from backend.agents.orchestrator.orchestrator_state import StepState


@dataclass(frozen=True)
class StepPhaseTransition:
    """Represents the timing for a completed step phase."""

    state: StepState
    started_at: datetime
    completed_at: datetime

    @property
    def duration_ms(self) -> int:
        """Return the total duration for the phase in milliseconds."""

        return max(0, int((self.completed_at - self.started_at).total_seconds() * 1000))


@dataclass(frozen=True)
class StepLifecycle:
    """Encapsulates allowed transitions between :class:`StepState` values."""

    transitions: Dict[StepState, StepState]

    def next_state(self, state: StepState) -> StepState:
        """Return the configured next state for ``state``."""

        return self.transitions[state]

    def iter_sequence(self, start: StepState) -> Iterable[StepState]:
        """Yield states from ``start`` until a terminal state is encountered."""

        current = start
        yield current
        while current in self.transitions:
            current = self.transitions[current]
            yield current


class StepLifecycleTracker:
    """Tracks timing information for step lifecycle phases."""

    def __init__(self) -> None:
        self._phase_started_at: Dict[StepState, datetime] = {}

    def start(self, state: StepState, *, timestamp: datetime | None = None) -> None:
        """Record the start time for ``state`` if not already tracked."""

        if state not in self._phase_started_at:
            self._phase_started_at[state] = timestamp or datetime.now(timezone.utc)

    def finish(self, state: StepState, *, timestamp: datetime | None = None) -> StepPhaseTransition:
        """Complete the timing for ``state`` and return the transition."""

        started_at = self._phase_started_at.setdefault(state, timestamp or datetime.now(timezone.utc))
        completed_at = timestamp or datetime.now(timezone.utc)
        transition = StepPhaseTransition(state=state, started_at=started_at, completed_at=completed_at)
        self._phase_started_at[state] = completed_at
        return transition


DEFAULT_STEP_LIFECYCLE = StepLifecycle(
    transitions={
        StepState.QUEUED: StepState.PLANNED,
        StepState.PLANNED: StepState.EXECUTING,
        StepState.EXECUTING: StepState.VALIDATING,
        StepState.VALIDATING: StepState.COMMITTING,
        StepState.COMMITTING: StepState.PR_UPDATED,
        StepState.PR_UPDATED: StepState.MERGED,
    }
)
