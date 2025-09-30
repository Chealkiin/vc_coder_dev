"""WorkOrder contract models."""

from __future__ import annotations

from typing import List, Literal
from uuid import UUID

from pydantic import Field

from .base import BaseContract
from .registry import register_contract
from .version import DEFAULT_VERSION


@register_contract(name="WorkOrder", version=DEFAULT_VERSION, aliases=["work_order"])
class WorkOrder(BaseContract):
    """Canonical work order payload."""

    work_order_id: UUID
    title: str
    objective: str
    constraints: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    context_files: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    return_format: Literal["unified-diff"]

