"""GitHub client configuration models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class GitHubConfig:
    """Configuration required to connect to a GitHub App installation.

    Attributes:
        app_id: Identifier for the GitHub App.
        installation_id: Identifier for the GitHub App installation.
        org: Optional organization slug if the app is scoped to an org.
        base_url: Optional base API URL for GitHub Enterprise deployments.
        repo: Target repository in the format ``"owner/name"``.
        base_ref: Branch that new feature branches should fork from.
        allow_auto_merge: Feature flag controlling automatic merges.
    """

    app_id: str
    installation_id: str
    org: Optional[str] = None
    base_url: Optional[str] = None
    repo: str = ""
    base_ref: str = ""
    allow_auto_merge: bool = False
