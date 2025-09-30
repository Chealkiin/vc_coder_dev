"""Implementation of the sub-planner adapter."""

from __future__ import annotations

from typing import Iterable, Mapping
from uuid import UUID

from core.contracts.work_order import WorkOrder

from .prompt_templates import build_planner_summary, build_work_order_brief


class BasicSubPlanner:
    """Normalize planner steps into canonical :class:`WorkOrder` payloads."""

    DEFAULT_DEPENDENCY_CONSTRAINT = "Do not add or modify dependencies."
    DEFAULT_RETURN_FORMAT = "unified-diff"
    DEFAULT_CONTEXT_ALLOWLIST: tuple[str, ...] = ("README.md", "docs/starter-spec.md")

    def __init__(self) -> None:
        self.transform_log: list[str] = []

    def _log(self, message: str) -> None:
        self.transform_log.append(message)

    def _coerce_uuid(self, value: object) -> UUID:
        if isinstance(value, UUID):
            return value
        if value is None:
            raise ValueError("Work order requires a work_order_id")
        return UUID(str(value))

    def _normalize_text(self, value: object, field_name: str) -> str:
        if value is None:
            raise ValueError(f"Work order requires field '{field_name}'")
        text = str(value).strip()
        if not text:
            raise ValueError(f"Work order field '{field_name}' cannot be empty")
        self._log(f"Normalized {field_name} whitespace")
        return text

    def _normalize_sequence(self, value: object, field_name: str) -> list[str]:
        items: list[str] = []
        if value is None:
            return items
        if isinstance(value, str):
            candidate = value.strip()
            if candidate:
                items.append(candidate)
        elif isinstance(value, Iterable):
            for entry in value:
                if entry is None:
                    continue
                candidate = str(entry).strip()
                if candidate:
                    items.append(candidate)
        else:
            candidate = str(value).strip()
            if candidate:
                items.append(candidate)
        if items:
            self._log(f"Normalized {field_name} list")
        return items

    def _extract_context_from_hints(self, step: Mapping[str, object]) -> list[str]:
        hints = step.get("hints")
        files: list[str] = []
        if isinstance(hints, Mapping):
            for key in ("files", "context_files"):
                hint_values = hints.get(key)
                if isinstance(hint_values, str):
                    candidate = hint_values.strip()
                    if candidate:
                        files.append(candidate)
                elif isinstance(hint_values, Iterable):
                    for value in hint_values:
                        if value is None:
                            continue
                        candidate = str(value).strip()
                        if candidate:
                            files.append(candidate)
        return files

    def _select_context_files(self, step: Mapping[str, object]) -> list[str]:
        provided = self._normalize_sequence(step.get("context_files"), "context_files")
        hints = self._extract_context_from_hints(step)
        selected: list[str] = []
        for path in provided + hints:
            if path not in selected:
                selected.append(path)
        if not selected:
            selected = list(self.DEFAULT_CONTEXT_ALLOWLIST)
            if selected:
                self._log("Defaulted context files to allowlist")
        else:
            self._log("Captured context files from step input")
        return selected

    def build_work_order(self, step: Mapping[str, object]) -> WorkOrder:
        """Return a canonical work order for ``step``."""

        self.transform_log = []

        work_order_id = self._coerce_uuid(
            step.get("work_order_id") or step.get("id")
        )
        title = self._normalize_text(step.get("title"), "title")
        objective = self._normalize_text(step.get("objective"), "objective")

        constraints = self._normalize_sequence(step.get("constraints"), "constraints")
        if not any(
            self.DEFAULT_DEPENDENCY_CONSTRAINT.lower() in item.lower()
            for item in constraints
        ):
            constraints.append(self.DEFAULT_DEPENDENCY_CONSTRAINT)
            self._log("Injected default dependency constraint")

        acceptance_criteria = self._normalize_sequence(
            step.get("acceptance_criteria"), "acceptance_criteria"
        )

        context_files = self._select_context_files(step)

        dependencies_allowed = bool(step.get("allow_dependency_changes"))
        dependencies = self._normalize_sequence(step.get("dependencies"), "dependencies")
        if not dependencies_allowed:
            if dependencies:
                self._log("Discarded dependency requests because they are not allowed")
            dependencies = []
        else:
            self._log("Preserved explicit dependency requests")

        work_order = WorkOrder(
            work_order_id=work_order_id,
            title=title,
            objective=objective,
            constraints=constraints,
            acceptance_criteria=acceptance_criteria,
            context_files=context_files,
            dependencies=dependencies,
            return_format=self.DEFAULT_RETURN_FORMAT,
        )

        self._log("Generated planner summary\n" + build_planner_summary(step))
        self._log(
            "Generated work order brief\n" + build_work_order_brief(work_order.to_dict())
        )
        return work_order
