"""Pydantic models describing validator output surfaces."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FatalItem(BaseModel):
    """Fatal validation finding that should block progress."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., description="Stable identifier for the failure class.")
    file: str = Field(
        ...,
        description="Repository-relative file path associated with the finding.",
    )
    line: int | None = Field(
        default=None,
        ge=1,
        description="1-indexed line number when available.",
    )
    msg: str = Field(..., description="Human-readable explanation of the failure.")


class WarningItem(BaseModel):
    """Non-blocking validation finding surfaced to operators."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., description="Stable identifier for the warning class.")
    file: str = Field(
        ...,
        description="Repository-relative file path associated with the warning.",
    )
    msg: str = Field(..., description="Human-readable explanation of the warning.")


class Metrics(BaseModel):
    """Execution metrics captured for validator runs."""

    model_config = ConfigDict(extra="forbid")

    lint_errors: int = Field(
        default=0,
        ge=0,
        description=(
            "Total number of lint/type errors encountered across validators."
        ),
    )
    tests_run: int = Field(
        default=0,
        ge=0,
        description=(
            "Number of automated tests executed within the validator workflow."
        ),
    )
    tests_failed: int = Field(
        default=0,
        ge=0,
        description=(
            "Number of automated tests that failed within the validator workflow."
        ),
    )


class ValidationReport(BaseModel):
    """Structured validator output returned to the orchestrator."""

    model_config = ConfigDict(extra="forbid")

    step_id: UUID = Field(
        ...,
        description="Identifier of the step associated with this report.",
    )
    fatal: list[FatalItem] = Field(
        default_factory=list,
        description="Fatal findings that should halt automated execution.",
    )
    warnings: list[WarningItem] = Field(
        default_factory=list,
        description="Warnings that inform operators without blocking execution.",
    )
    metrics: Metrics = Field(
        default_factory=Metrics,
        description="Validator metrics captured during execution.",
    )

    @property
    def has_fatal(self) -> bool:
        """Return True when any fatal findings are present."""

        return bool(self.fatal)


__all__ = ["FatalItem", "WarningItem", "Metrics", "ValidationReport"]
