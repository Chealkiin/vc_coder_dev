"""SQLAlchemy declarative base and model exports."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


from .artifact import Artifact, ArtifactKind
from .event import Event, EventType
from .run import PullRequestBinding, Run, RunStatus
from .step import Step, StepStatus
from .validation import ValidationReport

__all__ = [
    "Artifact",
    "ArtifactKind",
    "Base",
    "Event",
    "EventType",
    "NAMING_CONVENTION",
    "PullRequestBinding",
    "Run",
    "RunStatus",
    "Step",
    "StepStatus",
    "ValidationReport",
]
