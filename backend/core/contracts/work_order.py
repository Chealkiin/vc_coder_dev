"""Contracts for work order communication between agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class WorkOrder:
    """Normalized work order that coders consume.

    Attributes:
        step_id: Unique identifier of the run step.
        objectives: High-level goals for the coder to achieve.
        constraints: Explicit constraints limiting scope.
        acceptance_criteria: Formal acceptance criteria for validation.
        context_files: Repository-relative paths that provide necessary context.
        return_format: Required output format for the coder response.
        metadata: Optional additional metadata for downstream agents.
    """

    step_id: str
    objectives: List[str]
    constraints: List[str]
    acceptance_criteria: List[str]
    context_files: List[str]
    return_format: str
    metadata: Optional[Dict[str, object]]
