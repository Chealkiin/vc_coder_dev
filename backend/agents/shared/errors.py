"""Shared exception hierarchy for agent errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(eq=False)
class AgentError(Exception):
    """Base class for agent errors with metadata payloads."""

    message: str
    payload: Mapping[str, object] | None = None

    def __str__(self) -> str:
        """Render the message and payload for debugging."""

        if not self.payload:
            return self.message
        payload_str = ", ".join(f"{key}={value}" for key, value in self.payload.items())
        return f"{self.message} ({payload_str})"


class ValidationError(AgentError):
    """Raised when validation fails within an agent lifecycle."""


class OrchestratorError(AgentError):
    """Raised when the orchestrator encounters an unrecoverable issue."""

