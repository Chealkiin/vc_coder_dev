"""Coder adapter interface and helpers."""

from __future__ import annotations

from typing import Mapping, Protocol

from core.contracts.coder_result import CoderResult
from core.contracts.work_order import WorkOrder

from . import prompt_templates


class CoderAdapter(Protocol):
    """Interface for coder backends."""

    def execute(self, work_order: WorkOrder) -> CoderResult:
        """Execute ``work_order`` and return the resulting diff."""

    def build_coder_prompt(
        self, work_order: WorkOrder, repo_meta: Mapping[str, object] | None = None
    ) -> str:
        """Return the deterministic prompt for ``work_order``."""


class BaseCoderAdapter:
    """Base class implementing shared prompt helpers."""

    def execute(self, work_order: WorkOrder) -> CoderResult:
        """Execute the work order using a concrete coder backend."""

        raise NotImplementedError("Coder execution is not implemented in the base class")

    def build_coder_prompt(
        self, work_order: WorkOrder, repo_meta: Mapping[str, object] | None = None
    ) -> str:
        """Build the deterministic coder prompt for ``work_order``."""

        return prompt_templates.build_coder_prompt(work_order, repo_meta)
