"""Production orchestration agent coordinating planner, coder, and validator."""

from __future__ import annotations

import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Mapping, MutableMapping, Sequence, Tuple
from uuid import uuid4

from backend.agents.orchestrator.orchestrator_state import RunState, StepState
from backend.agents.orchestrator.policies import DEFAULT_MERGE_POLICY, MergeDecision, MergePolicy
from backend.agents.orchestrator.routing import (
    CoderAdapter,
    GitHubClient,
    PlannerAdapter,
    SubPlannerAdapter,
    ValidatorService,
)
from backend.agents.orchestrator.serialization import (
    persist_diff_artifact,
    persist_notes_artifact,
    persist_patch_summary,
    persist_validation_report,
)
from backend.agents.orchestrator.step_lifecycle import (
    DEFAULT_STEP_LIFECYCLE,
    StepLifecycle,
    StepLifecycleTracker,
    StepPhaseTransition,
)
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
    """Coordinates sequential execution of run steps with dependency injection."""

    _terminal_step_states: frozenset[StepState] = frozenset(
        {StepState.MERGED, StepState.PR_UPDATED, StepState.FAILED}
    )
    _completion_step_states: frozenset[StepState] = frozenset(
        {StepState.MERGED, StepState.PR_UPDATED}
    )

    def __init__(
        self,
        *,
        run_repo: RunRepo,
        step_repo: StepRepo,
        artifact_repo: ArtifactRepo,
        report_repo: ValidationReportRepo,
        pr_repo: PRBindingRepo,
        planner_adapter: PlannerAdapter,
        sub_planner_adapter: SubPlannerAdapter,
        coder_adapter: CoderAdapter,
        validator_service: ValidatorService,
        github_client: GitHubClient,
        events: EventsPublisher,
        logger: logging.Logger,
        config: Mapping[str, object],
        lifecycle: StepLifecycle | None = None,
        merge_policy: MergePolicy | None = None,
    ) -> None:
        self._run_repo = run_repo
        self._step_repo = step_repo
        self._artifact_repo = artifact_repo
        self._report_repo = report_repo
        self._pr_repo = pr_repo
        self._planner = planner_adapter
        self._sub_planner = sub_planner_adapter
        self._coder = coder_adapter
        self._validator = validator_service
        self._github = github_client
        self._events = events
        self.logger = logger
        self._config = config
        self._lifecycle = lifecycle or DEFAULT_STEP_LIFECYCLE
        self._merge_policy = merge_policy or DEFAULT_MERGE_POLICY
        self.agent_name = self.__class__.__name__

    # ---------------------------------------------------------------------
    # Run lifecycle
    # ---------------------------------------------------------------------
    def start_run(
        self,
        repo: str,
        base_ref: str,
        steps: Sequence[Mapping[str, object]],
    ) -> str:
        """Create run and step records before beginning execution."""

        feature_ref = self._derive_feature_branch()
        run_id = self._run_repo.create_run(
            repo=repo,
            base_ref=base_ref,
            feature_ref=feature_ref,
            status=RunState.QUEUED,
            config=self._config,
        )
        normalized_steps = [self._normalize_step(run_id, index, step) for index, step in enumerate(steps)]
        self._step_repo.create_steps(run_id, normalized_steps)
        self._run_repo.update_run_state(run_id, RunState.RUNNING)
        self._emit_run_state(run_id, RunState.RUNNING, meta={"from_state": RunState.QUEUED.value})
        return run_id

    def pause_run(self, run_id: str) -> None:
        """Pause execution for the run."""

        self._run_repo.update_run_state(run_id, RunState.PAUSED)
        self._emit_run_state(run_id, RunState.PAUSED)

    def resume_run(self, run_id: str) -> None:
        """Resume execution for a previously paused run."""

        self._run_repo.update_run_state(run_id, RunState.RUNNING)
        self._emit_run_state(run_id, RunState.RUNNING)

    # ------------------------------------------------------------------
    # Step lifecycle
    # ------------------------------------------------------------------
    def advance_step(self, run_id: str) -> StepState:
        """Advance the next available step through the orchestrator pipeline."""

        run_snapshot = self._run_repo.get_run(run_id)
        if not run_snapshot:
            raise OrchestratorError("run_not_found", payload={"run_id": run_id})

        steps = list(self._step_repo.list_steps(run_id))
        if not steps:
            raise OrchestratorError("no_steps_defined", payload={"run_id": run_id})

        next_step = self._select_next_step(steps)
        if not next_step:
            self._maybe_complete_run(run_id, steps)
            raise OrchestratorError("no_pending_steps", payload={"run_id": run_id})

        step_index, step_record = next_step
        step_state = self._extract_state(step_record)
        step_id = str(step_record["id"])
        tracker = StepLifecycleTracker()

        try:
            final_state = self._execute_step_pipeline(
                run_id=run_id,
                run_snapshot=run_snapshot,
                step_index=step_index,
                step_id=step_id,
                step_record=step_record,
                starting_state=step_state,
                tracker=tracker,
            )
        except Exception as exc:  # pragma: no cover - exercised via tests
            self._handle_step_failure(run_id, step_id, step_record, exc)
            return StepState.FAILED

        self._maybe_complete_run(run_id, self._step_repo.list_steps(run_id))
        return final_state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _execute_step_pipeline(
        self,
        *,
        run_id: str,
        run_snapshot: Mapping[str, object],
        step_index: int,
        step_id: str,
        step_record: Mapping[str, object],
        starting_state: StepState,
        tracker: StepLifecycleTracker,
    ) -> StepState:
        current_state = StepState.QUEUED if starting_state == StepState.PAUSED else starting_state
        next_state = self._determine_next_state(current_state)
        planner_output: Mapping[str, object] | object | None = None
        work_order: object | None = None
        coder_result: object | None = None
        validation_report: Mapping[str, object] | object | None = None

        while next_state:
            if next_state == StepState.PLANNED:
                tracker.start(next_state)
                planner_output = self._planner.plan_step(step_record)
                if self._is_work_order(planner_output):
                    work_order = planner_output
                    planner_payload: MutableMapping[str, object] = dict(
                        self._coerce_mapping(planner_output)
                    )
                else:
                    planner_payload = dict(planner_output)
                if work_order is None:
                    work_order = self._sub_planner.build_work_order(planner_payload)
                self._step_repo.update_step_metadata(
                    run_id,
                    step_id,
                    plan=planner_payload,
                    work_order=dict(self._coerce_mapping(work_order)),
                )
                self._step_repo.update_step_state(run_id, step_id, StepState.PLANNED)
                transition = tracker.finish(next_state)
                self._emit_step_event(
                    run_id,
                    step_id,
                    next_state,
                    transition,
                    meta={"step_index": step_index},
                )
                current_state = next_state
                next_state = self._determine_next_state(current_state)
                continue

            if next_state == StepState.EXECUTING:
                tracker.start(next_state)
                if work_order is None:
                    raise OrchestratorError(
                        "work_order_missing",
                        payload={"run_id": run_id, "step_id": step_id},
                    )
                coder_result = self._coder.execute(work_order)
                self._step_repo.update_step_metadata(
                    run_id,
                    step_id,
                    coder_result=dict(self._coerce_mapping(coder_result)),
                )
                diff_text = str(self._get_attr(coder_result, "diff", ""))
                persist_diff_artifact(
                    self._artifact_repo,
                    run_id=run_id,
                    step_id=step_id,
                    diff=diff_text,
                )
                persist_notes_artifact(
                    self._artifact_repo,
                    run_id=run_id,
                    step_id=step_id,
                    notes=self._get_attr(coder_result, "notes"),
                )
                self._step_repo.update_step_state(run_id, step_id, StepState.EXECUTING)
                transition = tracker.finish(next_state)
                self._emit_step_event(
                    run_id,
                    step_id,
                    next_state,
                    transition,
                    meta={"step_index": step_index},
                )
                current_state = next_state
                next_state = self._determine_next_state(current_state)
                continue

            if next_state == StepState.VALIDATING:
                tracker.start(next_state)
                if coder_result is None:
                    raise OrchestratorError(
                        "coder_result_missing",
                        payload={"run_id": run_id, "step_id": step_id},
                    )
                base_ref = str(run_snapshot.get("base_ref"))
                feature_ref = str(run_snapshot.get("feature_ref"))
                diff_text = str(self._get_attr(coder_result, "diff", ""))
                validation_report = self._validator.validate(
                    diff_text,
                    base_ref,
                    feature_ref,
                )
                persist_validation_report(
                    self._report_repo,
                    run_id=run_id,
                    step_id=step_id,
                    report=dict(self._coerce_mapping(validation_report)),
                )
                self._step_repo.update_step_state(run_id, step_id, StepState.VALIDATING)
                transition = tracker.finish(next_state)
                self._emit_step_event(
                    run_id,
                    step_id,
                    StepState.VALIDATING,
                    transition,
                    meta={
                        "step_index": step_index,
                        "fatal": len(self._extract_sequence(validation_report, "fatal")),
                    },
                )
                if self._extract_sequence(validation_report, "fatal"):
                    self._step_repo.update_step_state(run_id, step_id, StepState.PAUSED)
                    self._run_repo.update_run_state(run_id, RunState.PAUSED)
                    pause_transition = tracker.finish(StepState.PAUSED)
                    self._emit_step_event(
                        run_id,
                        step_id,
                        StepState.PAUSED,
                        pause_transition,
                        meta={"reason": "validation_fatal", "step_index": step_index},
                    )
                    self._emit_run_state(run_id, RunState.PAUSED)
                    return StepState.PAUSED
                current_state = next_state
                next_state = self._determine_next_state(current_state)
                continue

            if next_state == StepState.COMMITTING:
                tracker.start(next_state)
                if coder_result is None:
                    raise OrchestratorError(
                        "coder_result_missing",
                        payload={"run_id": run_id, "step_id": step_id},
                    )
                base_ref = str(run_snapshot.get("base_ref"))
                feature_ref = str(run_snapshot.get("feature_ref"))
                self._github.ensure_branch(base_ref, feature_ref)
                diff_text = str(self._get_attr(coder_result, "diff", ""))
                patch_summary_raw = self._github.apply_patch(feature_ref, diff_text)
                patch_summary = self._coerce_mapping(patch_summary_raw)
                persist_patch_summary(
                    self._artifact_repo,
                    run_id=run_id,
                    step_id=step_id,
                    summary=patch_summary,
                )
                self._step_repo.update_step_state(run_id, step_id, StepState.COMMITTING)
                transition = tracker.finish(next_state)
                self._emit_step_event(
                    run_id,
                    step_id,
                    StepState.COMMITTING,
                    transition,
                    meta={"step_index": step_index, "patch": dict(patch_summary)},
                )
                current_state = next_state
                next_state = self._determine_next_state(current_state)
                continue

            if next_state == StepState.PR_UPDATED:
                tracker.start(next_state)
                final_state, decision = self._handle_pr_update(
                    run_id=run_id,
                    run_snapshot=run_snapshot,
                    step_record=step_record,
                    step_id=step_id,
                    validation_report=validation_report,
                )
                transition = tracker.finish(next_state)
                self._emit_step_event(
                    run_id,
                    step_id,
                    final_state,
                    transition,
                    meta={
                        "step_index": step_index,
                        "merge_action": decision.action,
                        "merge_reason": decision.reason,
                    },
                )
                return final_state

            break

        return current_state

    def _handle_pr_update(
        self,
        *,
        run_id: str,
        run_snapshot: Mapping[str, object],
        step_record: Mapping[str, object],
        step_id: str,
        validation_report: Mapping[str, object] | object | None,
    ) -> Tuple[StepState, MergeDecision]:
        base_ref = str(run_snapshot.get("base_ref"))
        feature_ref = str(run_snapshot.get("feature_ref"))
        pr_binding = self._pr_repo.get(run_id)
        pr_title = self._build_pr_title(run_snapshot, step_record)
        pr_body = self._render_pr_body(step_record, validation_report)

        if pr_binding:
            pr_number = int(pr_binding["pr_number"])
            self._github.update_pr_body(pr_number, pr_body)
        else:
            pr_number, pr_url = self._github.create_or_update_pr(
                pr_title,
                pr_body,
                feature_ref,
                base_ref,
            )
            self._pr_repo.upsert(
                run_id,
                {"pr_number": pr_number, "pr_url": pr_url, "head": feature_ref, "base": base_ref},
            )

        self._step_repo.update_step_state(run_id, step_id, StepState.PR_UPDATED)
        report_payload = validation_report or {
            "step_id": str(uuid4()),
            "fatal": [],
            "warnings": [],
            "metrics": {},
        }
        decision = self._merge_policy.evaluate(self._config, report_payload, step_record)

        if decision.action == "auto":
            self._step_repo.update_step_state(run_id, step_id, StepState.MERGED)
            return StepState.MERGED, decision

        if decision.action == "blocked":
            self._step_repo.update_step_state(run_id, step_id, StepState.PAUSED)
            self._run_repo.update_run_state(run_id, RunState.PAUSED)
            self._emit_run_state(run_id, RunState.PAUSED)
            return StepState.PAUSED, decision

        return StepState.PR_UPDATED, decision

    def _determine_next_state(self, current: StepState) -> StepState | None:
        try:
            return self._lifecycle.next_state(current)
        except KeyError:
            return None

    def _select_next_step(
        self, steps: Sequence[Mapping[str, object]]
    ) -> Tuple[int, Mapping[str, object]] | None:
        for index, step in enumerate(steps):
            state = self._extract_state(step)
            if state in self._terminal_step_states:
                continue
            return index, step
        return None

    def _extract_state(self, step: Mapping[str, object]) -> StepState:
        try:
            return StepState(str(step.get("state", StepState.QUEUED.value)))
        except ValueError as exc:  # pragma: no cover - defensive
            raise OrchestratorError("invalid_step_state", payload={"step": step}) from exc

    def _handle_step_failure(
        self,
        run_id: str,
        step_id: str,
        step_record: Mapping[str, object],
        exc: Exception,
    ) -> None:
        self._step_repo.update_step_state(run_id, step_id, StepState.FAILED)
        now = datetime.now(timezone.utc)
        transition = StepPhaseTransition(
            state=StepState.FAILED,
            started_at=now,
            completed_at=now,
        )
        self._emit_step_event(
            run_id,
            step_id,
            StepState.FAILED,
            transition,
            meta={"error": exc.__class__.__name__},
        )
        self.log_json(
            logging.ERROR,
            "step_failed",
            run_id=run_id,
            step_id=step_id,
            phase=StepState.FAILED.value,
            meta={"error": str(exc)},
        )

    def _maybe_complete_run(self, run_id: str, steps: Sequence[Mapping[str, object]]) -> None:
        if all(self._extract_state(step) in self._completion_step_states for step in steps):
            self._run_repo.update_run_state(run_id, RunState.COMPLETED)
            self._emit_run_state(run_id, RunState.COMPLETED)

    def _emit_step_event(
        self,
        run_id: str,
        step_id: str,
        state: StepState,
        transition: StepPhaseTransition,
        meta: Mapping[str, object] | None = None,
    ) -> None:
        event = self._build_step_event(run_id, step_id, state, transition, meta)
        self._events.publish(event)
        self.log_json(
            logging.INFO,
            "step_state_changed",
            run_id=run_id,
            step_id=step_id,
            phase=state.value,
            meta={"duration_ms": transition.duration_ms, **(dict(meta or {}))},
        )

    def _build_step_event(
        self,
        run_id: str,
        step_id: str,
        state: StepState,
        transition: StepPhaseTransition,
        meta: Mapping[str, object] | None,
    ) -> LifecycleEvent:
        event_cls = self._event_class_for_state(state)
        return event_cls(
            run_id=run_id,
            step_id=step_id,
            state=state.value,
            timestamp=transition.completed_at,
            duration_ms=transition.duration_ms,
            meta=meta,
        )

    def _emit_run_state(
        self,
        run_id: str,
        state: RunState,
        meta: Mapping[str, object] | None = None,
    ) -> None:
        event = RunStatusChanged(
            run_id=run_id,
            step_id=None,
            state=state.value,
            timestamp=datetime.now(timezone.utc),
            meta=meta,
        )
        self._events.publish(event)
        self.log_json(
            logging.INFO,
            "run_state_changed",
            run_id=run_id,
            phase=state.value,
            meta=meta or {},
        )

    def _event_class_for_state(self, state: StepState) -> type[LifecycleEvent]:
        mapping = {
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

    def _derive_feature_branch(self) -> str:
        prefix = str(self._config.get("feature_branch", "autogen/feature"))
        suffix = uuid4().hex[:8]
        return f"{prefix}-{suffix}" if prefix else suffix

    def _normalize_step(
        self,
        run_id: str,
        index: int,
        step: Mapping[str, object],
    ) -> Mapping[str, object]:
        normalized: MutableMapping[str, object] = dict(step)
        normalized.setdefault("id", f"{run_id}-step-{index}")
        normalized.setdefault("index", index)
        normalized.setdefault("state", StepState.QUEUED.value)
        normalized.setdefault("title", f"Step {index + 1}")
        normalized.setdefault("body", "")
        return normalized

    def _coerce_mapping(self, payload: object) -> Mapping[str, object]:
        if isinstance(payload, Mapping):
            return payload
        to_dict = getattr(payload, "to_dict", None)
        if callable(to_dict):
            return to_dict()
        model_dump = getattr(payload, "model_dump", None)
        if callable(model_dump):
            return model_dump()
        if is_dataclass(payload):
            return asdict(payload)
        if hasattr(payload, "__dict__"):
            return {key: value for key, value in vars(payload).items() if not key.startswith("_")}
        raise OrchestratorError("unsupported_summary_payload", payload={"type": type(payload).__name__})

    @staticmethod
    def _get_attr(payload: object, attribute: str, default: object | None = None) -> object | None:
        if isinstance(payload, Mapping):
            return payload.get(attribute, default)
        return getattr(payload, attribute, default)

    @staticmethod
    def _extract_sequence(payload: Mapping[str, object] | object, attribute: str) -> list[object]:
        value = None
        if isinstance(payload, Mapping):
            value = payload.get(attribute)
        else:
            value = getattr(payload, attribute, None)
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        return []

    @staticmethod
    def _is_work_order(payload: object | None) -> bool:
        if payload is None:
            return False
        if isinstance(payload, Mapping):
            return False
        return hasattr(payload, "work_order_id") and (
            callable(getattr(payload, "to_dict", None))
            or callable(getattr(payload, "model_dump", None))
        )

    def _build_pr_title(
        self,
        run_snapshot: Mapping[str, object],
        step_record: Mapping[str, object],
    ) -> str:
        repo = str(run_snapshot.get("repo", ""))
        title = str(step_record.get("title", "")) or "Automated update"
        return f"{title} ({repo})" if repo else title

    def _render_pr_body(
        self,
        step_record: Mapping[str, object],
        validation_report: Mapping[str, object] | object | None,
    ) -> str:
        summary_lines = [f"## Step: {step_record.get('title', 'Untitled Step')}\n"]
        summary_lines.append(step_record.get("body", ""))
        report = (
            dict(self._coerce_mapping(validation_report))
            if validation_report is not None
            else {"fatal": [], "warnings": []}
        )
        summary_lines.append("\n## Validation\n")
        summary_lines.append(f"Fatal issues: {len(report.get('fatal', []))}\n")
        summary_lines.append(f"Warnings: {len(report.get('warnings', []))}\n")
        return "\n".join(summary_lines)
