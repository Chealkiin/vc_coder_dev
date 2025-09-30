"""Coder result contract."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from .base import BaseContract
from .registry import register_contract
from .version import DEFAULT_VERSION


@register_contract(name="CoderResult", version=DEFAULT_VERSION, aliases=["coder_result"])
class CoderResult(BaseContract):
    """Payload returned by the coding agent."""

    work_order_id: UUID
    diff: str
    notes: Optional[str] = None

