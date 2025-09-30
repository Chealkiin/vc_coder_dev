"""SQLAlchemy model for lifecycle events."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, Optional

import uuid

from sqlalchemy import BigInteger, Enum as SAEnum, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from backend.core.events.lifecycle import LifecycleEventType


class EventType(str, Enum):
    """Enumeration of persisted event types."""

    RUN_CREATED = LifecycleEventType.RUN_CREATED.value
    RUN_COMPLETED = LifecycleEventType.RUN_COMPLETED.value
    STEP_PLANNED = LifecycleEventType.STEP_PLANNED.value
    STEP_EXECUTING = LifecycleEventType.STEP_EXECUTING.value
    STEP_VALIDATED = LifecycleEventType.STEP_VALIDATED.value
    STEP_FAILED = LifecycleEventType.STEP_FAILED.value
    STEP_COMMITTED = LifecycleEventType.STEP_COMMITTED.value
    STEP_MERGED = LifecycleEventType.STEP_MERGED.value


class Event(Base):
    """Persistence model representing run and step lifecycle events."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("steps.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    type: Mapped[EventType] = mapped_column(
        SAEnum(EventType, name="event_type", native_enum=False, validate_strings=True),
        nullable=False,
    )
    payload: Mapped[Dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    ts: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    run: Mapped["Run"] = relationship(
        "Run",
        back_populates="events",
        passive_deletes=True,
    )
    step: Mapped[Optional["Step"]] = relationship(
        "Step",
        back_populates="events",
        passive_deletes=True,
    )


__all__ = ["Event", "EventType"]
