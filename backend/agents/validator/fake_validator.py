"""Validator fake that always succeeds while surfacing informational warnings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping
from uuid import UUID, uuid5

from backend.agents.orchestrator.routing import ValidatorService

_VALIDATION_NAMESPACE = UUID("87654321-4321-8765-4321-876543218765")


@dataclass(frozen=True)
class FakeValidationReport:
    """Minimal validation report used by the demo orchestrator wiring."""

    step_id: str
    fatal: List[Mapping[str, object]]
    warnings: List[Mapping[str, object]]
    metrics: Mapping[str, object]
    fatal_count: int
    warnings_count: int

    def to_dict(self) -> Mapping[str, object]:
        """Return a mapping representation compatible with the repo interface."""

        return {
            "step_id": self.step_id,
            "fatal": list(self.fatal),
            "warnings": list(self.warnings),
            "metrics": dict(self.metrics),
            "fatal_count": self.fatal_count,
            "warnings_count": self.warnings_count,
        }


class FakeValidator(ValidatorService):
    """Validator fake that records metrics but never blocks progress."""

    def validate(self, diff: str, base_ref: str, feature_ref: str) -> FakeValidationReport:
        """Return a validation report with warnings but no fatal issues."""

        warnings: List[Mapping[str, object]] = []
        if diff:
            warnings.append(
                {
                    "code": "INFO_PLACEHOLDER",
                    "file": "frontend/app/settings.tsx",
                    "msg": "Reminder: replace placeholder copy before shipping.",
                }
            )
        report_id = str(uuid5(_VALIDATION_NAMESPACE, feature_ref))
        metrics = {"lint_errors": 0, "tests_run": 0, "tests_failed": 0}
        return FakeValidationReport(
            step_id=report_id,
            fatal=[],
            warnings=warnings,
            metrics=metrics,
            fatal_count=0,
            warnings_count=len(warnings),
        )


__all__ = ["FakeValidationReport", "FakeValidator"]
