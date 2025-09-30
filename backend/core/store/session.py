"""Database session management utilities for Postgres."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_ENGINE: Engine | None = None
_SessionFactory: sessionmaker | None = None


def configure_engine(dsn: str) -> None:
    """Configure the global SQLAlchemy engine.

    Args:
        dsn: Database connection string.

    Note:
        # TODO(team, 2024-05-22): Harden connection pooling and retries for production.
    """

    global _ENGINE, _SessionFactory
    _ENGINE = create_engine(dsn, pool_pre_ping=True, future=True)
    _SessionFactory = sessionmaker(bind=_ENGINE, class_=Session, expire_on_commit=False)


def get_engine() -> Engine:
    """Return the configured SQLAlchemy engine.

    Returns:
        A SQLAlchemy engine instance.

    Raises:
        RuntimeError: If the engine has not been configured.
    """

    if _ENGINE is None:
        raise RuntimeError("Database engine is not configured.")
    return _ENGINE


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.

    Yields:
        A SQLAlchemy session.

    Raises:
        RuntimeError: If the session factory has not been configured.
    """

    if _SessionFactory is None:
        raise RuntimeError("Session factory is not configured.")
    session: Session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()
