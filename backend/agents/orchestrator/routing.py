"""Protocol definitions for orchestrator dependency injection."""

from __future__ import annotations

from typing import Mapping, Protocol, runtime_checkable


class WorkOrderPayload(Protocol):
    """Minimal interface of a work order payload."""

    work_order_id: object

    def to_dict(self) -> Mapping[str, object]:
        """Return a dictionary representation of the work order."""


class CoderResultPayload(Protocol):
    """Minimal interface of coder results."""

    work_order_id: object
    diff: str
    notes: str | None

    def to_dict(self) -> Mapping[str, object]:
        """Return a dictionary representation of the coder result."""


class ValidationReportPayload(Protocol):
    """Minimal interface of validation reports."""

    fatal: object
    warnings: object

    def to_dict(self) -> Mapping[str, object]:
        """Return a dictionary representation of the validation report."""


@runtime_checkable
class PlannerAdapter(Protocol):
    """Adapter responsible for high level step planning."""

    def plan_step(self, step: Mapping[str, object]) -> Mapping[str, object] | WorkOrderPayload:
        """Produce a normalized representation of the work required for ``step``."""


@runtime_checkable
class SubPlannerAdapter(Protocol):
    """Adapter responsible for turning planner output into a concrete work order."""

    def build_work_order(self, step: Mapping[str, object]) -> WorkOrderPayload:
        """Return a canonical :class:`~core.contracts.WorkOrder` for the provided ``step``."""


@runtime_checkable
class CoderAdapter(Protocol):
    """Adapter that executes the work order and returns coder output."""

    def execute(self, work_order: WorkOrderPayload) -> CoderResultPayload:
        """Execute ``work_order`` and return the resulting diff and notes."""


@runtime_checkable
class ValidatorService(Protocol):
    """Service that validates coder output before committing changes."""

    def validate(
        self,
        diff: str,
        base_ref: str,
        feature_ref: str,
    ) -> ValidationReportPayload | Mapping[str, object]:
        """Run validations on ``diff`` against ``base_ref`` and ``feature_ref``."""


@runtime_checkable
class GitHubClient(Protocol):
    """Client abstraction for interacting with GitHub without performing real calls."""

    def ensure_branch(self, base_ref: str, feature_ref: str) -> None:
        """Ensure that ``feature_ref`` exists for the run."""

    def apply_patch(self, feature_ref: str, unified_diff: str) -> Mapping[str, object]:
        """Apply ``unified_diff`` to ``feature_ref`` and return a patch summary."""

    def create_or_update_pr(
        self,
        title: str,
        body_md: str,
        head: str,
        base: str,
    ) -> tuple[int, str]:
        """Create or update a pull request and return ``(number, url)``."""

    def update_pr_body(self, pr_number: int, body_md: str) -> None:
        """Update the body of an existing pull request."""
