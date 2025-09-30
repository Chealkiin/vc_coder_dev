"""Repository interfaces for persistence operations."""

from __future__ import annotations

from typing import Protocol

from backend.core.models.artifact import Artifact
from backend.core.models.run import Run
from backend.core.models.step import Step
from backend.core.models.validation import ValidationReport


class RunRepository(Protocol):
    """Persistence operations for runs."""

    def create(self, run: Run) -> Run:
        """Persist a new run entity."""
        ...

    def get(self, run_id: str) -> Run:
        """Retrieve a run by identifier."""
        ...


class StepRepository(Protocol):
    """Persistence operations for steps."""

    def create(self, step: Step) -> Step:
        """Persist a new step entity."""
        ...

    def update(self, step: Step) -> Step:
        """Update an existing step entity."""
        ...

    def get(self, step_id: str) -> Step:
        """Retrieve a step by identifier."""
        ...


class ArtifactRepository(Protocol):
    """Persistence operations for artifacts."""

    def create(self, artifact: Artifact) -> Artifact:
        """Persist a new artifact entity."""
        ...


class EventRepository(Protocol):
    """Persistence operations for lifecycle events."""

    def publish(self, event_payload: dict) -> None:
        """Persist a lifecycle event payload."""
        ...


class ValidationReportRepository(Protocol):
    """Persistence operations for validation reports."""

    def upsert(self, step_id: str, report: ValidationReport) -> ValidationReport:
        """Persist or update a validation report."""
        ...


class PullRequestBindingRepository(Protocol):
    """Persistence operations for PR bindings."""

    def upsert(self, run_id: str, pr_number: int, branch: str) -> None:
        """Persist or update the PR binding for a run."""
        ...
