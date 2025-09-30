"""SQLAlchemy models for validation reports."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict

from sqlalchemy import ForeignKey, Integer, func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class ValidationReport(Base):
    """Persistence model capturing validator outputs for a step."""

    __tablename__ = "validation_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    step_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report: Mapped[Dict[str, object]] = mapped_column(JSONB, nullable=False)
    fatal_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    warnings_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    step: Mapped["Step"] = relationship(
        "Step",
        back_populates="validation_reports",
        passive_deletes=True,
    )


__all__ = ["ValidationReport"]
