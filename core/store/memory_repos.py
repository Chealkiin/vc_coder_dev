"""In-memory repositories used by the demo orchestrator wiring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import count
from typing import Collection, Dict, Iterable, List, Mapping, MutableMapping, Sequence

from backend.agents.orchestrator.orchestrator_state import RunState, StepState
from core.store.repositories import ArtifactRepo, PRBindingRepo, RunRepo, StepRepo, ValidationReportRepo


@dataclass
class RunRecord:
    """Representation of a run persisted in memory."""

    run_id: str
    repo: str
    base_ref: str
    feature_ref: str
    status: RunState
    config: Mapping[str, object]
    created_at: datetime
    updated_at: datetime
    meta: MutableMapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> Mapping[str, object]:
        """Return a serialisable snapshot of the run."""

        return {
            "id": self.run_id,
            "repo": self.repo,
            "base_ref": self.base_ref,
            "feature_ref": self.feature_ref,
            "status": self.status,
            "config": dict(self.config),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "meta": dict(self.meta),
        }


@dataclass
class StepRecord:
    """Representation of a run step tracked in memory."""

    run_id: str
    step_id: str
    index: int
    title: str
    body: str
    state: StepState
    created_at: datetime
    updated_at: datetime
    plan: MutableMapping[str, object] | None = None
    work_order: MutableMapping[str, object] | None = None
    coder_result: MutableMapping[str, object] | None = None

    def to_dict(self) -> Mapping[str, object]:
        """Return a mapping copy suitable for repository consumers."""

        payload: MutableMapping[str, object] = {
            "id": self.step_id,
            "index": self.index,
            "title": self.title,
            "body": self.body,
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.plan is not None:
            payload["plan"] = dict(self.plan)
        if self.work_order is not None:
            payload["work_order"] = dict(self.work_order)
        if self.coder_result is not None:
            payload["coder_result"] = dict(self.coder_result)
        return payload


@dataclass
class ArtifactRecord:
    """Artifact snapshot persisted by :class:`InMemoryArtifactRepo`."""

    artifact_id: str
    run_id: str
    step_id: str
    kind: str
    content: str
    meta: Mapping[str, object]
    created_at: datetime

    def to_dict(self) -> Mapping[str, object]:
        """Return a mapping representation for assertions and debugging."""

        return {
            "id": self.artifact_id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "kind": self.kind,
            "content": self.content,
            "meta": dict(self.meta),
            "created_at": self.created_at,
        }


@dataclass
class ValidationReportRecord:
    """Validation report snapshot tracked for demo purposes."""

    report_id: str
    run_id: str
    step_id: str
    report: Mapping[str, object]
    fatal_count: int
    warnings_count: int
    created_at: datetime

    def to_dict(self) -> Mapping[str, object]:
        """Return a copy of the stored validation report."""

        return {
            "id": self.report_id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "report": dict(self.report),
            "fatal_count": self.fatal_count,
            "warnings_count": self.warnings_count,
            "created_at": self.created_at,
        }


class InMemoryRunRepo(RunRepo):
    """In-memory implementation of :class:`RunRepo` for demos and tests."""

    def __init__(self) -> None:
        self._runs: Dict[str, RunRecord] = {}
        self._counter = count(1)

    def create_run(
        self,
        *,
        repo: str,
        base_ref: str,
        feature_ref: str,
        status: RunState,
        config: Mapping[str, object] | None = None,
    ) -> str:
        run_index = next(self._counter)
        run_id = f"run-{run_index:04d}"
        now = datetime.now(timezone.utc)
        record = RunRecord(
            run_id=run_id,
            repo=repo,
            base_ref=base_ref,
            feature_ref=feature_ref,
            status=status,
            config=dict(config or {}),
            created_at=now,
            updated_at=now,
        )
        self._runs[run_id] = record
        return run_id

    def get_run(self, run_id: str) -> Mapping[str, object] | None:
        record = self._runs.get(run_id)
        return record.to_dict() if record else None

    def update_run_state(self, run_id: str, state: RunState) -> None:
        record = self._runs[run_id]
        record.status = state
        record.updated_at = datetime.now(timezone.utc)

    def list_runs(self) -> Sequence[Mapping[str, object]]:
        """Return all stored runs for inspection."""

        return [record.to_dict() for record in self._runs.values()]


class InMemoryStepRepo(StepRepo):
    """In-memory implementation of :class:`StepRepo`."""

    def __init__(self) -> None:
        self._steps: Dict[str, List[StepRecord]] = {}

    def create_steps(
        self, run_id: str, steps: Sequence[Mapping[str, object]]
    ) -> Sequence[Mapping[str, object]]:
        now = datetime.now(timezone.utc)
        stored: List[StepRecord] = []
        for step in steps:
            step_id = str(step.get("id"))
            stored.append(
                StepRecord(
                    run_id=run_id,
                    step_id=step_id,
                    index=int(step.get("index", len(stored))),
                    title=str(step.get("title", "")),
                    body=str(step.get("body", "")),
                    state=StepState(step.get("state", StepState.QUEUED.value)),
                    created_at=now,
                    updated_at=now,
                )
            )
        self._steps[run_id] = stored
        return [record.to_dict() for record in stored]

    def list_steps(self, run_id: str) -> Sequence[Mapping[str, object]]:
        return [record.to_dict() for record in self._steps.get(run_id, [])]

    def update_step_state(self, run_id: str, step_id: str, state: StepState) -> None:
        for record in self._steps.get(run_id, []):
            if record.step_id == step_id:
                record.state = state
                record.updated_at = datetime.now(timezone.utc)
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
        for record in self._steps.get(run_id, []):
            if record.step_id != step_id:
                continue
            if plan is not None:
                record.plan = dict(plan)
            if work_order is not None:
                record.work_order = dict(work_order)
            if coder_result is not None:
                record.coder_result = dict(coder_result)
            record.updated_at = datetime.now(timezone.utc)
            break

    def list_step_states(self, run_id: str) -> Iterable[StepState]:
        """Yield the current states for each step in ``run_id``."""

        for record in self._steps.get(run_id, []):
            yield record.state


class InMemoryArtifactRepo(ArtifactRepo):
    """In-memory implementation of :class:`ArtifactRepo`."""

    def __init__(self) -> None:
        self._artifacts: List[ArtifactRecord] = []
        self._counter = count(1)

    def add(
        self,
        *,
        run_id: str,
        step_id: str,
        kind: str,
        content: str,
        meta: Mapping[str, object] | None = None,
    ) -> None:
        artifact_id = f"artifact-{next(self._counter):04d}"
        record = ArtifactRecord(
            artifact_id=artifact_id,
            run_id=run_id,
            step_id=step_id,
            kind=kind,
            content=content,
            meta=dict(meta or {}),
            created_at=datetime.now(timezone.utc),
        )
        self._artifacts.append(record)

    def list_artifacts(self, step_id: str) -> Sequence[Mapping[str, object]]:
        """Return artifacts associated with ``step_id``."""

        return [record.to_dict() for record in self._artifacts if record.step_id == step_id]

    def all_artifacts(self) -> Sequence[Mapping[str, object]]:
        """Return all stored artifacts."""

        return [record.to_dict() for record in self._artifacts]


class InMemoryValidationReportRepo(ValidationReportRepo):
    """In-memory implementation of :class:`ValidationReportRepo`."""

    def __init__(self) -> None:
        self._reports: List[ValidationReportRecord] = []
        self._counter = count(1)

    def add(
        self,
        *,
        run_id: str,
        step_id: str,
        report: Mapping[str, object],
    ) -> None:
        fatal = report.get("fatal")
        warnings = report.get("warnings")
        fatal_count = self._safe_len(fatal)
        warnings_count = self._safe_len(warnings)
        record = ValidationReportRecord(
            report_id=f"report-{next(self._counter):04d}",
            run_id=run_id,
            step_id=step_id,
            report=dict(report),
            fatal_count=fatal_count,
            warnings_count=warnings_count,
            created_at=datetime.now(timezone.utc),
        )
        self._reports.append(record)

    def list_reports(self, run_id: str | None = None) -> Sequence[Mapping[str, object]]:
        """Return stored reports, optionally filtered by ``run_id``."""

        records = self._reports
        if run_id is not None:
            records = [record for record in records if record.run_id == run_id]
        return [record.to_dict() for record in records]

    @staticmethod
    def _safe_len(candidate: object | None) -> int:
        """Return ``len(candidate)`` when the value behaves like a collection."""

        if candidate is None:
            return 0
        if isinstance(candidate, (str, bytes)):
            return 0
        if isinstance(candidate, Collection):
            return len(candidate)
        if isinstance(candidate, Iterable):
            return sum(1 for _ in candidate)
        return 0


class InMemoryPRBindingRepo(PRBindingRepo):
    """In-memory implementation of :class:`PRBindingRepo`."""

    def __init__(self) -> None:
        self._bindings: Dict[str, Mapping[str, object]] = {}

    def get(self, run_id: str) -> Mapping[str, object] | None:
        return self._bindings.get(run_id)

    def upsert(self, run_id: str, metadata: Mapping[str, object]) -> None:
        self._bindings[run_id] = dict(metadata)

    def list_bindings(self) -> Mapping[str, Mapping[str, object]]:
        """Return all stored PR bindings."""

        return {run_id: dict(metadata) for run_id, metadata in self._bindings.items()}


__all__ = [
    "InMemoryArtifactRepo",
    "InMemoryPRBindingRepo",
    "InMemoryRunRepo",
    "InMemoryStepRepo",
    "InMemoryValidationReportRepo",
    "RunRecord",
    "StepRecord",
    "ArtifactRecord",
    "ValidationReportRecord",
]
