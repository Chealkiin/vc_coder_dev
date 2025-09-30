"""Structured logging utilities for backend services."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

_LOGGER_CACHE: Dict[str, logging.Logger] = {}


class JsonLogFormatter(logging.Formatter):
    """JSON formatter that enforces structured log output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record into a JSON string.

        Args:
            record: A standard logging record.

        Returns:
            A JSON-formatted string representing the log entry.
        """

        payload = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "meta": getattr(record, "meta", {}),
        }
        return json.dumps(payload, sort_keys=True)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a module-level structured logger instance.

    Args:
        name: Logger name.
        level: Logging level for the logger.

    Returns:
        A configured logger emitting structured JSON entries.
    """

    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    logger.handlers = [handler]
    logger.propagate = False
    _LOGGER_CACHE[name] = logger
    return logger


def add_context(logger: logging.Logger, *, run_id: Optional[str] = None, step_id: Optional[str] = None) -> logging.LoggerAdapter:
    """Attach run and step context metadata to a logger.

    Args:
        logger: The base logger instance.
        run_id: Optional run identifier for context.
        step_id: Optional step identifier for context.

    Returns:
        A logger adapter that enriches log entries with contextual metadata.
    """

    extra: Dict[str, Any] = {"meta": {}}
    if run_id:
        extra["meta"]["run_id"] = run_id
    if step_id:
        extra["meta"]["step_id"] = step_id
    return logging.LoggerAdapter(logger, extra)
