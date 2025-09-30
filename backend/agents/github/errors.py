"""GitHub client exceptions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class GitHubError(Exception):
    """Base exception for GitHub client operations."""

    message: str
    meta: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


@dataclass(slots=True)
class PatchApplyError(GitHubError):
    """Raised when a patch cannot be applied cleanly."""

    failed_paths: Optional[list[str]] = None
