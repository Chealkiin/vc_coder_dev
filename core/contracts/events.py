"""Event payload contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from pydantic import Field

from .base import BaseContract
from .registry import register_contract
from .version import DEFAULT_VERSION


@register_contract(
    name="StepStatusPayload",
    version=DEFAULT_VERSION,
    aliases=["step_status", "step_status_payload"],
)
class StepStatusPayload(BaseContract):
    """Payload published to the event bus for step status updates."""

    run_id: UUID
    step_id: UUID
    state: str
    timestamps: Dict[str, datetime] = Field(default_factory=dict)
    durations_ms: Dict[str, float] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)

