"""State machine utilities for orchestrator step progression."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from backend.agents.orchestrator.orchestrator_state import StepState


@dataclass(frozen=True)
class StepLifecycle:
    """Encapsulates the minimal deterministic step state machine."""

    transitions: Dict[StepState, StepState]

    def next_state(self, state: StepState) -> StepState:
        """Return the next state in the lifecycle.

        Args:
            state: Current state of the step.

        Returns:
            The subsequent state as defined by ``transitions``.

        Raises:
            KeyError: If the transition is undefined.
        """

        return self.transitions[state]


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

