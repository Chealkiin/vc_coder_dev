"""Diff size guard utilities for validator executions."""

from __future__ import annotations

import os
from dataclasses import dataclass

from backend.agents.validator.report_model import FatalItem


@dataclass
class DiffSummary:
    """Aggregated information about the current diff under validation."""

    total_changed_lines: int
    new_files_count: int


def guards_enabled() -> bool:
    """Return True when diff size guards should run."""

    value = os.getenv("SIZE_GUARDS_ENABLED", "true").lower()
    return value not in {"0", "false", "no"}


def max_changed_lines() -> int:
    """Return the configured maximum changed lines threshold."""

    try:
        return int(os.getenv("MAX_CHANGED_LINES", "5000"))
    except ValueError:
        return 5000


def max_new_files() -> int:
    """Return the configured maximum new files threshold."""

    try:
        return int(os.getenv("MAX_NEW_FILES", "50"))
    except ValueError:
        return 50


def check_diff_size(summary: DiffSummary) -> FatalItem | None:
    """Check diff summary against configured size thresholds."""

    if not guards_enabled():
        return None

    over_lines = summary.total_changed_lines > max_changed_lines()
    over_files = summary.new_files_count > max_new_files()

    if not (over_lines or over_files):
        return None

    reasons = []
    if over_lines:
        reasons.append(
            "changed lines "
            f"{summary.total_changed_lines} exceeds limit {max_changed_lines()}"
        )
    if over_files:
        reasons.append(
            "new files "
            f"{summary.new_files_count} exceeds limit {max_new_files()}"
        )

    message = "Diff size guard triggered: " + "; ".join(reasons)
    return FatalItem(code="SIZE_GUARD", file="", line=None, msg=message)


__all__ = [
    "DiffSummary",
    "check_diff_size",
    "guards_enabled",
    "max_changed_lines",
    "max_new_files",
]
