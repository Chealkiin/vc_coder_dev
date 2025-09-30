"""SQLAlchemy models for run entities."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class RunStatus(str, Enum):
    """Enumeration of run lifecycle states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Run(Base):
    """Persistence model representing a workflow run."""

    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    repo: Mapped[str] = mapped_column(Text, nullable=False)
    base_ref: Mapped[str] = mapped_column(Text, nullable=False)
    branch_ref: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, name="run_status", native_enum=False, validate_strings=True),
        nullable=False,
        default=RunStatus.PENDING,
        server_default=text("'pending'"),
    )
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

    steps: Mapped[List["Step"]] = relationship(
        "Step",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    pull_request_binding: Mapped[Optional["PullRequestBinding"]] = relationship(
        "PullRequestBinding",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    events: Mapped[List["Event"]] = relationship(
        "Event",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PullRequestBinding(Base):
    """Persistence model mapping runs to GitHub pull requests."""

    __tablename__ = "pr_bindings"

    run_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pr_url: Mapped[str] = mapped_column(Text, nullable=False)

    run: Mapped[Run] = relationship(
        "Run",
        back_populates="pull_request_binding",
        passive_deletes=True,
    )


__all__ = ["Run", "RunStatus", "PullRequestBinding"]
