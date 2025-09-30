"""Coder adapter stubs."""

from __future__ import annotations

from typing import Protocol

from backend.core.contracts.work_order import WorkOrder


class CoderAdapter(Protocol):
    """Defines the coder adapter interface."""

    def execute(self, work_order: WorkOrder) -> str:
        """Execute the work order and return a unified diff."""


def execute(work_order: WorkOrder) -> str:
    """Execute a work order using the configured coder backend.

    Args:
        work_order: The work order to execute.

    Returns:
        Unified diff text representing the proposed changes.

    Note:
        # TODO(team, 2024-05-22): Integrate Codex client and repository context streaming.
    """

    raise NotImplementedError("Coder adapter is not yet implemented.")
