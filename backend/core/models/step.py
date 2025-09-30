"""Run step model definitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Step:
    """Represents a single step within a run.

    Attributes:
        id: Unique identifier for the step.
        run_id: Identifier of the owning run.
        created_at: Creation timestamp in UTC.
        updated_at: Last update timestamp in UTC.
        status: Step lifecycle status.
        payload: Serialized step definition payload.
        result_metadata: Optional metadata from downstream agents.
    """

    id: str
    run_id: str
    created_at: datetime
    updated_at: datetime
    status: str
    payload: Dict[str, object]
    result_metadata: Optional[Dict[str, object]]
