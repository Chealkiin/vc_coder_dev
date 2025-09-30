"""Production ready orchestrator skeleton with dependency injection."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Mapping, Sequence, cast

from backend.agents.orchestrator.orchestrator_state import RunState, StepState
from backend.agents.orchestrator.step_lifecycle import DEFAULT_STEP_LIFECYCLE, StepLifecycle
from backend.agents.shared.errors import OrchestratorError
from backend.agents.shared.logging_mixin import LoggingMixin
from core.events import EventsPublisher
from core.events.types import (
    LifecycleEvent,
    RunStatusChanged,
    StepCommitted,
    StepExecuting,
    StepFailed,
    StepPaused,
    StepPlanned,
    StepValidated,
)
from core.store.repositories import ArtifactRepo, PRBindingRepo, RunRepo, StepRepo, ValidationReportRepo


class OrchestratorAgent(LoggingMixin):
    """Coordinates the execution of run steps and emits lifecycle events."""

    _terminal_states: frozenset[StepState] = frozenset({StepState.MERGED, StepState.FAILED})

    def __init__(
        self,
        *,
        run_repo: RunRepo,
        step_repo: StepRepo,
        artifact_repo: ArtifactRepo,
        validation_report_repo: ValidationReportRepo,
        pr_binding_repo: PRBindingRepo,
        events_publisher: EventsPublisher,
        logger: logging.Logger,
        lifecycle: StepLifecycle | None = None,
    ) -> None:
        """Inject dependencies required for orchestration.

        Args:
            run_repo: Repository used to persist run metadata.
            step_repo: Repository used to persist step metadata.
            artifact_repo: Repository for artifacts (placeholder for future logic).
            validation_report_repo: Repository for validation reports.
            pr_binding_repo: Repository for PR binding metadata.
            events_publisher: Publisher used to emit lifecycle events.
            logger: Structured logger for observability.
            lifecycle: Optional override for the step lifecycle state machine.
        """

        self._run_repo = run_repo
        self._step_repo = step_repo
        self._artifact_repo = artifact_repo
        self._validation_report_repo = validation_report_repo
        self._pr_binding_repo = pr_binding_repo
        self._events_publisher = events_publisher
        self.logger = logger
        self._lifecycle = lifecycle or DEFAULT_STEP_LIFECYCLE
        self.agent_name = self.__class__.__name__

    def start_run(self, repo: str, base_ref: str, steps: Sequence[Mapping[str, object]]) -> str:
        """Create the run entry and seed steps in the store.

        Args:
            repo: Repository slug that triggered the run.
            base_ref: Branch or commit the run is based on.
            steps: Declarative step definitions.

        Returns:
            Identifier of the newly created run.
        """

        run_id = self._run_repo.create_run(repo, base_ref, steps)
        self._step_repo.create_steps(run_id, steps)
        self._run_repo.update_run_state(run_id, RunState.RUNNING)
        self._emit_run_state(run_id, RunState.RUNNING)
        return run_id

    def pause_run(self, run_id: str) -> None:
        """Persist pause state for a run and emit a lifecycle event."""

        self._run_repo.update_run_state(run_id, RunState.PAUSED)
        self._emit_run_state(run_id, RunState.PAUSED)

    def resume_run(self, run_id: str) -> None:
        """Resume a previously paused run."""

        self._run_repo.update_run_state(run_id, RunState.RUNNING)
        self._emit_run_state(run_id, RunState.RUNNING)

    def retry_step(self, run_id: str, index: int) -> StepState:
        """Reset a step state to ``QUEUED`` for retry."""

        self._step_repo.update_step_state(run_id, index, StepState.QUEUED)
        return StepState.QUEUED

    def advance_step(self, run_id: str) -> StepState:
        """Advance the next pending step and emit associated event."""

        steps = list(self._step_repo.list_steps(run_id))
        if not steps:
            raise OrchestratorError("No steps available to advance", payload={"run_id": run_id})

        for index, step in enumerate(steps):
            state_value = cast(str, step["state"])  # Protocol guarantees mapping semantics
            current_state = StepState(state_value)
            if current_state in self._terminal_states:
                continue
            next_state = self._lifecycle.next_state(current_state)
            self._step_repo.update_step_state(run_id, index, next_state)
            self._emit_step_event(run_id, step, index, next_state)
            self._maybe_complete_run(run_id, steps, index, next_state)
            return next_state

        # All steps terminal
        self._maybe_complete_run(run_id, steps, len(steps) - 1, StepState.MERGED)
        raise OrchestratorError(
            "All steps are already terminal",
            payload={"run_id": run_id},
        )

    def _maybe_complete_run(
        self,
        run_id: str,
        steps: Sequence[Mapping[str, object]],
        index: int,
        latest_state: StepState,
    ) -> None:
        observed_states = [
            latest_state if idx == index else self._state_from_mapping(step)
            for idx, step in enumerate(steps)
        ]
        if all(self._is_terminal_state(state) for state in observed_states if state is not None):
            self._run_repo.update_run_state(run_id, RunState.COMPLETED)
            self._emit_run_state(run_id, RunState.COMPLETED)
        elif latest_state == StepState.PAUSED:
            self._run_repo.update_run_state(run_id, RunState.PAUSED)
            self._emit_run_state(run_id, RunState.PAUSED)
        elif latest_state == StepState.FAILED:
            self._run_repo.update_run_state(run_id, RunState.FAILED)
            self._emit_run_state(run_id, RunState.FAILED)

    def _emit_step_event(
        self,
        run_id: str,
        step: Mapping[str, object],
        index: int,
        state: StepState,
    ) -> None:
        event = self._build_step_event(run_id, step, index, state)
        self._events_publisher.publish(event)
        self.log_json(
            logging.INFO,
            "step_state_changed",
            run_id=run_id,
            step_id=self._extract_step_id(step, index),
            phase=state.value,
            meta={"state": state.value},
        )

    def _emit_run_state(self, run_id: str, state: RunState) -> None:
        event = RunStatusChanged(
            run_id=run_id,
            step_id=None,
            state=state.value,
            timestamp=datetime.now(timezone.utc),
        )
        self._events_publisher.publish(event)
        self.log_json(
            logging.INFO,
            "run_state_changed",
            run_id=run_id,
            phase=state.value,
            meta={"state": state.value},
        )

    def _build_step_event(
        self,
        run_id: str,
        step: Mapping[str, object],
        index: int,
        state: StepState,
    ) -> LifecycleEvent:
        event_cls = self._event_class_for_state(state)
        return event_cls(
            run_id=run_id,
            step_id=self._extract_step_id(step, index),
            state=state.value,
            timestamp=datetime.now(timezone.utc),
        )

    def _event_class_for_state(self, state: StepState) -> type[LifecycleEvent]:
        mapping: Dict[StepState, type[LifecycleEvent]] = {
            StepState.PLANNED: StepPlanned,
            StepState.EXECUTING: StepExecuting,
            StepState.VALIDATING: StepValidated,
            StepState.COMMITTING: StepCommitted,
            StepState.PR_UPDATED: StepCommitted,
            StepState.MERGED: StepCommitted,
            StepState.PAUSED: StepPaused,
            StepState.FAILED: StepFailed,
        }
        return mapping.get(state, StepExecuting)

    def _extract_step_id(self, step: Mapping[str, object], index: int) -> str:
        identifier = step.get("id") or step.get("step_id") or step.get("name")
        if isinstance(identifier, str):
            return identifier
        return f"{index}"

    def _is_terminal_state(self, state: StepState | None) -> bool:
        return state is not None and state in self._terminal_states

    def _state_from_mapping(self, step: Mapping[str, object]) -> StepState | None:
        try:
            return StepState(cast(str, step["state"]))
        except (KeyError, ValueError):
            return None

