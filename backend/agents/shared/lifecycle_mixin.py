"""Lifecycle scaffolding shared across agent implementations."""

from __future__ import annotations

from typing import Mapping


class LifecycleMixin:
    """Provides strongly-typed lifecycle hooks for agents.

    Each hook intentionally defaults to a no-op so that concrete agents can
    override only the phases they need. The hooks enforce the canonical
    lifecycle contract of ``prepare -> build_context -> execute -> postprocess``
    which keeps the orchestration pipeline deterministic and testable.
    """

    def prepare(self, run_id: str, step_id: str | None = None) -> None:
        """Perform synchronous setup before any heavy computation.

        Args:
            run_id: Identifier for the run orchestrated by the caller.
            step_id: Optional identifier for a step scoped to the run.
        """

    def build_context(self, run_id: str, step_id: str | None = None) -> Mapping[str, object]:
        """Assemble the execution context consumed by :meth:`execute`.

        Args:
            run_id: Identifier for the active run.
            step_id: Optional identifier for the active step.

        Returns:
            Mapping containing the context information. The default
            implementation returns an empty mapping which is sufficient for
            lightweight agents or tests.
        """

        return {}

    def execute(self, context: Mapping[str, object]) -> Mapping[str, object]:  # pragma: no cover - abstract default
        """Execute the core agent logic.

        Args:
            context: Context assembled by :meth:`build_context`.

        Returns:
            Mapping that contains the primary result of the execution.

        Raises:
            NotImplementedError: The base mixin does not implement execution
            and concrete agents are expected to provide the behavior.
        """

        raise NotImplementedError("Concrete agents must implement execute().")

    def postprocess(self, context: Mapping[str, object], result: Mapping[str, object]) -> Mapping[str, object]:
        """Perform cleanup or result augmentation after :meth:`execute`.

        Args:
            context: Context object that was passed to :meth:`execute`.
            result: Result returned by :meth:`execute`.

        Returns:
            Mapping representing the final payload. The default implementation
            returns ``result`` unchanged which satisfies most agents.
        """

        return result

