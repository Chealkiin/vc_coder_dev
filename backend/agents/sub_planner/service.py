"""Sub-planner agent interface stubs."""

from __future__ import annotations

from typing import Protocol

from backend.core.contracts.work_order import WorkOrder
from backend.core.models.step import Step


class SubPlannerService(Protocol):
    """Defines the sub-planner interface for producing detailed work orders."""

    def plan(self, step: Step) -> WorkOrder:
        """Produce a detailed work order for the given step."""


def plan(step: Step) -> WorkOrder:
    """Plan a step at the sub-task granularity.

    Args:
        step: The run step requiring additional decomposition.

    Returns:
        A work order containing coder-ready instructions.

    Note:
        # TODO(team, 2024-05-22): Implement sub-planner prompting with constraint enforcement.
    """

    raise NotImplementedError("Sub-planner implementation is pending.")
