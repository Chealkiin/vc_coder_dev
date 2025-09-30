"""Artifact model definitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Artifact:
    """Represents an artifact generated during a run step.

    Attributes:
        id: Unique identifier for the artifact.
        run_id: Associated run identifier.
        step_id: Associated step identifier.
        created_at: Creation timestamp in UTC.
        artifact_type: Type descriptor (e.g., diff, log, asset).
        storage_url: Location where the artifact is persisted.
        metadata: Optional metadata for consumers.
    """

    id: str
    run_id: str
    step_id: str
    created_at: datetime
    artifact_type: str
    storage_url: str
    metadata: Optional[Dict[str, object]]
