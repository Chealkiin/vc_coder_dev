"""Repository stubs for database persistence."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from backend.core.models.artifact import Artifact, ArtifactKind
from backend.core.models.event import Event, EventType
from backend.core.models.run import PullRequestBinding, Run, RunStatus
from backend.core.models.step import Step, StepStatus
from backend.core.models.validation import ValidationReport


class RunRepository:
    """CRUD operations for run aggregates."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, repo: str, base_ref: str, branch_ref: str) -> Run:
        """Persist a new run entity."""

        raise NotImplementedError

    def get(self, run_id: uuid.UUID) -> Optional[Run]:
        """Retrieve a run by identifier."""

        raise NotImplementedError

    def list(self) -> Sequence[Run]:
        """List all persisted runs."""

        raise NotImplementedError

    def update_status(self, run_id: uuid.UUID, status: RunStatus) -> Run:
        """Update the status of an existing run."""

        raise NotImplementedError

    def delete(self, run_id: uuid.UUID) -> None:
        """Delete a run and cascade to dependents."""

        raise NotImplementedError


class StepRepository:
    """CRUD operations for run steps."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        run_id: uuid.UUID,
        idx: int,
        title: str,
        body: str,
        status: StepStatus = StepStatus.PENDING,
    ) -> Step:
        """Persist a new step for a run."""

        raise NotImplementedError

    def get(self, step_id: uuid.UUID) -> Optional[Step]:
        """Fetch a step by identifier."""

        raise NotImplementedError

    def list_for_run(self, run_id: uuid.UUID) -> Sequence[Step]:
        """List all steps for a given run."""

        raise NotImplementedError

    def update_status(self, step_id: uuid.UUID, status: StepStatus) -> Step:
        """Update the lifecycle status for a step."""

        raise NotImplementedError

    def delete(self, step_id: uuid.UUID) -> None:
        """Remove a step and its dependents."""

        raise NotImplementedError


class ArtifactRepository:
    """CRUD operations for artifacts."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        step_id: uuid.UUID,
        kind: ArtifactKind,
        uri: str,
        meta: Optional[dict] = None,
    ) -> Artifact:
        """Persist a new artifact for a step."""

        raise NotImplementedError

    def get(self, artifact_id: uuid.UUID) -> Optional[Artifact]:
        """Retrieve an artifact by identifier."""

        raise NotImplementedError

    def list_for_step(self, step_id: uuid.UUID) -> Sequence[Artifact]:
        """List artifacts associated with a step."""

        raise NotImplementedError

    def delete(self, artifact_id: uuid.UUID) -> None:
        """Delete an artifact."""

        raise NotImplementedError


class ValidationReportRepository:
    """CRUD operations for validation reports."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        step_id: uuid.UUID,
        report: dict,
        fatal_count: int = 0,
        warnings_count: int = 0,
    ) -> ValidationReport:
        """Persist a validation report for a step."""

        raise NotImplementedError

    def get(self, report_id: uuid.UUID) -> Optional[ValidationReport]:
        """Retrieve a validation report by identifier."""

        raise NotImplementedError

    def get_for_step(self, step_id: uuid.UUID) -> Optional[ValidationReport]:
        """Retrieve the latest validation report for a step."""

        raise NotImplementedError

    def update_counts(
        self,
        report_id: uuid.UUID,
        *,
        fatal_count: int,
        warnings_count: int,
    ) -> ValidationReport:
        """Update aggregated counts for a validation report."""

        raise NotImplementedError

    def delete(self, report_id: uuid.UUID) -> None:
        """Delete a validation report."""

        raise NotImplementedError


class PullRequestBindingRepository:
    """CRUD operations for pull request bindings."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def bind(self, run_id: uuid.UUID, pr_number: int, pr_url: str) -> PullRequestBinding:
        """Create or update a PR binding for a run."""

        raise NotImplementedError

    def get(self, run_id: uuid.UUID) -> Optional[PullRequestBinding]:
        """Retrieve the PR binding for a run."""

        raise NotImplementedError

    def delete(self, run_id: uuid.UUID) -> None:
        """Remove the PR binding for a run."""

        raise NotImplementedError


class EventRepository:
    """CRUD operations for lifecycle events."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        *,
        run_id: uuid.UUID,
        step_id: Optional[uuid.UUID],
        event_type: EventType,
        payload: Optional[dict] = None,
    ) -> Event:
        """Persist a lifecycle event."""

        raise NotImplementedError

    def list_for_run(self, run_id: uuid.UUID) -> Sequence[Event]:
        """List events associated with a run."""

        raise NotImplementedError

    def delete_for_run(self, run_id: uuid.UUID) -> None:
        """Delete all events for a run."""

        raise NotImplementedError

    def purge_before(self, threshold_ts: datetime) -> int:
        """Delete events older than a timestamp threshold."""

        raise NotImplementedError
