"""Planner agent interface stubs."""

from __future__ import annotations

from typing import Protocol

from backend.core.contracts.work_order import WorkOrder
from backend.core.models.step import Step


class PlannerService(Protocol):
    """Defines the planner interface for producing work orders."""

    def plan(self, step: Step) -> WorkOrder:
        """Produce a work order for the given step."""


def plan(step: Step) -> WorkOrder:
    """Plan a run step and return a work order.

    Args:
        step: The run step requiring planning.

    Returns:
        A work order describing coder objectives.

    Note:
        # TODO(team, 2024-05-22): Implement planner integration with task design prompts.
    """

    raise NotImplementedError("Planner implementation is pending.")
