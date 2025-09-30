"""Run model definitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Run:
    """Represents a top-level execution run for the orchestrator.

    Attributes:
        id: Unique identifier for the run.
        created_at: Creation timestamp in UTC.
        updated_at: Last update timestamp in UTC.
        status: High-level status (e.g., pending, running, completed).
        metadata: Optional JSON-serializable metadata payload.
    """

    id: str
    created_at: datetime
    updated_at: datetime
    status: str
    metadata: Optional[Dict[str, object]]
