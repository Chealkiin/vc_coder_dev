"""Interfaces for routing orchestration tasks to specialized adapters."""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence


class PlannerAdapter(Protocol):
    """Plans the high level steps for an orchestration run."""

    def plan(self, run_id: str, repo: str, base_ref: str, steps: Sequence[Mapping[str, object]]) -> Sequence[Mapping[str, object]]:
        """Return an ordered list of steps to execute."""


class SubPlannerAdapter(Protocol):
    """Plans fine-grained sub-steps for a specific step."""

    def plan_step(self, run_id: str, step_id: str, context: Mapping[str, object]) -> Sequence[Mapping[str, object]]:
        """Return sub-step descriptors for downstream agents."""


class CoderAdapter(Protocol):
    """Executes coding tasks for a planned step."""

    def apply(self, run_id: str, step_id: str, instructions: Mapping[str, object]) -> Mapping[str, object]:
        """Return artifacts resulting from the coding step."""

