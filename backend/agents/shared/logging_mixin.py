"""Structured logging mixin for agent implementations."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Mapping


class LoggingMixin:
    """Provides JSON structured logging aligned with production requirements."""

    logger: logging.Logger

    def log_json(
        self,
        level: int,
        message: str,
        *,
        run_id: str | None = None,
        step_id: str | None = None,
        phase: str | None = None,
        meta: Mapping[str, object] | None = None,
    ) -> None:
        """Emit a structured log entry.

        Args:
            level: Logging level (e.g. ``logging.INFO``).
            message: Human readable message summarizing the event.
            run_id: Optional run identifier for correlation.
            step_id: Optional step identifier for correlation.
            phase: Lifecycle phase that triggered the log entry.
            meta: Arbitrary serializable metadata to attach to the entry.
        """

        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": logging.getLevelName(level),
            "run_id": run_id,
            "step_id": step_id,
            "agent": getattr(self, "agent_name", self.__class__.__name__),
            "phase": phase,
            "message": message,
            "meta": dict(meta or {}),
        }
        self.logger.log(level, json.dumps(payload, default=str))

