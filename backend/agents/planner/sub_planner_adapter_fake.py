"""Deterministic fake sub-planner for the happy-path demo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping, MutableMapping
from uuid import UUID, uuid5

from backend.agents.orchestrator.routing import SubPlannerAdapter

_NAMESPACE = UUID("12345678-1234-5678-1234-567812345678")


@dataclass(frozen=True)
class DemoWorkOrder:
    """Minimal work-order payload returned by :class:`SubPlannerAdapterFake`."""

    work_order_id: str
    title: str
    objective: str
    constraints: List[str]
    acceptance_criteria: List[str]
    context_files: List[str]
    return_format: str
    metadata: Mapping[str, object]

    def to_dict(self) -> Mapping[str, object]:
        """Return a serialisable representation consumed by repositories."""

        return {
            "work_order_id": self.work_order_id,
            "title": self.title,
            "objective": self.objective,
            "constraints": list(self.constraints),
            "acceptance_criteria": list(self.acceptance_criteria),
            "context_files": list(self.context_files),
            "return_format": self.return_format,
            "metadata": dict(self.metadata),
        }


class SubPlannerAdapterFake(SubPlannerAdapter):
    """Fake sub-planner that normalises step text deterministically."""

    def __init__(self) -> None:
        self.transform_log: List[str] = []

    def build_work_order(self, step: Mapping[str, object]) -> DemoWorkOrder:
        """Return a deterministic :class:`DemoWorkOrder` for ``step``."""

        self.transform_log = []
        step_id = str(step.get("id") or "demo-step")
        work_order_id = str(uuid5(_NAMESPACE, step_id))
        title = self._normalize_text(step.get("title"), field_name="title")
        objective = self._normalize_text(step.get("body"), field_name="body")

        constraints = self._normalize_sequence(step.get("constraints"), default="Return a unified diff")
        acceptance = self._normalize_sequence(step.get("acceptance_criteria"), default="Diff applies cleanly")
        context_files = self._normalize_sequence(step.get("context_files"), default="README.md")

        metadata: MutableMapping[str, object] = {"transform_log": list(self.transform_log)}

        return DemoWorkOrder(
            work_order_id=work_order_id,
            title=title,
            objective=objective,
            constraints=constraints,
            acceptance_criteria=acceptance,
            context_files=context_files,
            return_format="unified-diff",
            metadata=metadata,
        )

    def _normalize_text(self, value: object | None, *, field_name: str) -> str:
        """Trim whitespace while recording why normalisation occurred."""

        text = (str(value or "")).strip()
        if not text:
            self.transform_log.append(f"Defaulted missing {field_name}")
            return f"Demo {field_name.capitalize()}"
        if value != text:
            self.transform_log.append(f"Trimmed {field_name} whitespace")
        return text

    def _normalize_sequence(self, value: object | None, *, default: str) -> List[str]:
        """Return a list of normalised strings with deterministic fallback."""

        items: List[str] = []
        if value is None:
            items.append(default)
            self.transform_log.append(f"Injected default for {default}")
            return items

        if isinstance(value, str):
            candidate = value.strip()
            if candidate:
                items.append(candidate)
        elif isinstance(value, Mapping):
            for entry in value.values():
                candidate = str(entry).strip()
                if candidate:
                    items.append(candidate)
        elif isinstance(value, (list, tuple, set)):
            for entry in value:
                candidate = str(entry).strip()
                if candidate:
                    items.append(candidate)
        else:
            candidate = str(value).strip()
            if candidate:
                items.append(candidate)

        if not items:
            items.append(default)
            self.transform_log.append(f"Injected default for {default}")
        else:
            self.transform_log.append(f"Normalised sequence for default={default}")
        return items


__all__ = ["DemoWorkOrder", "SubPlannerAdapterFake"]
