"""Validation report model definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ValidationMessage:
    """Represents a single validation message entry."""

    code: str
    file: str
    message: str


@dataclass
class ValidationReport:
    """Represents the validator output for a set of changes."""

    fatal: List[ValidationMessage] = field(default_factory=list)
    warnings: List[ValidationMessage] = field(default_factory=list)
    metrics: Dict[str, int] = field(default_factory=dict)
