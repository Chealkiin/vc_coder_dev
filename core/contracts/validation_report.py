"""Validation report contract."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseContract
from .registry import register_contract
from .version import DEFAULT_VERSION


class Issue(BaseModel):
    """Validation issue description."""

    model_config = ConfigDict(extra="forbid", frozen=False, ser_json_inf_nan='null')

    code: str
    file: Optional[str] = None
    line: Optional[int] = None
    msg: str


@register_contract(name="ValidationReport", version=DEFAULT_VERSION, aliases=["validation_report"])
class ValidationReport(BaseContract):
    """Validator output surface."""

    step_id: UUID
    fatal: List[Issue] = Field(default_factory=list)
    warnings: List[Issue] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

