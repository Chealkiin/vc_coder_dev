"""SQLAlchemy models for run steps."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class StepStatus(str, Enum):
    """Enumeration of step lifecycle states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Step(Base):
    """Persistence model representing a unit of work within a run."""

    __tablename__ = "steps"
    __table_args__ = (UniqueConstraint("run_id", "idx"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[StepStatus] = mapped_column(
        SAEnum(StepStatus, name="step_status", native_enum=False, validate_strings=True),
        nullable=False,
        default=StepStatus.PENDING,
        server_default=text("'pending'"),
    )
    acceptance_criteria: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    plan_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    run: Mapped["Run"] = relationship(
        "Run",
        back_populates="steps",
        passive_deletes=True,
    )
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact",
        back_populates="step",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    validation_reports: Mapped[List["ValidationReport"]] = relationship(
        "ValidationReport",
        back_populates="step",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    events: Mapped[List["Event"]] = relationship(
        "Event",
        back_populates="step",
        passive_deletes=True,
    )


__all__ = ["Step", "StepStatus"]
