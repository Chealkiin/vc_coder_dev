"""Database session management utilities for Postgres."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def configure_engine(dsn: str | None = None) -> None:
    """Configure the global SQLAlchemy engine.

    Args:
        dsn: Optional database connection string. If omitted, ``DB_DSN`` is read from
            the environment.

    Raises:
        RuntimeError: If no DSN is provided or found in the environment.

    Note:
        # TODO(team, 2024-05-22): Harden connection pooling and retries for production.
    """

    database_dsn = dsn or os.getenv("DB_DSN")
    if not database_dsn:
        raise RuntimeError("DB_DSN environment variable is required to configure the engine.")

    global _ENGINE, _SESSION_FACTORY
    _ENGINE = create_engine(database_dsn, pool_pre_ping=True, future=True)
    _SESSION_FACTORY = sessionmaker(bind=_ENGINE, class_=Session, expire_on_commit=False)


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

    if _SESSION_FACTORY is None:
        raise RuntimeError("Session factory is not configured.")
    session: Session = _SESSION_FACTORY()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_factory() -> sessionmaker[Session]:
    """Return the configured session factory."""

    if _SESSION_FACTORY is None:
        raise RuntimeError("Session factory is not configured.")
    return _SESSION_FACTORY
