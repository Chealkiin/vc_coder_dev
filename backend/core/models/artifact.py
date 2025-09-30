"""SQLAlchemy models for step artifacts."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class ArtifactKind(str, Enum):
    """Enumeration of artifact classifications."""

    DIFF = "diff"
    DOC = "doc"
    LOG = "log"
    BLOB = "blob"
    REJECTION = "rej"


class Artifact(Base):
    """Persistence model for artifacts generated during a step."""

    __tablename__ = "artifacts"

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
    kind: Mapped[ArtifactKind] = mapped_column(
        SAEnum(ArtifactKind, name="artifact_kind", native_enum=False, validate_strings=True),
        nullable=False,
    )
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[Dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    step: Mapped["Step"] = relationship(
        "Step",
        back_populates="artifacts",
        passive_deletes=True,
    )


__all__ = ["Artifact", "ArtifactKind"]
