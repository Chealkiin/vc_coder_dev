"""Validator service stubs."""

from __future__ import annotations

from collections.abc import Iterable

from backend.core.models.validation import ValidationReport


def validate(changed_paths: Iterable[str]) -> ValidationReport:
    """Validate changed paths and produce a report.

    Args:
        changed_paths: Iterable of repository-relative paths.

    Returns:
        Validation report containing fatal errors and warnings.

    Note:
        # TODO(team, 2024-05-22): Integrate language-specific linters and tests.
    """

    raise NotImplementedError("Validator implementation is pending.")
