"""GitHub integration stubs."""

from __future__ import annotations

from typing import Protocol


class GitHubIntegrator(Protocol):
    """Defines operations for interacting with GitHub."""

    def create_branch(self, base_ref: str, feature_ref: str) -> None:
        """Create a feature branch from the specified base reference."""

    def apply_patch(self, diff: str) -> None:
        """Apply a unified diff to the feature branch."""

    def create_or_update_pr(self, *, title: str, body: str, head: str, base: str) -> int:
        """Create or update a pull request and return its number."""


def create_branch(base_ref: str, feature_ref: str) -> None:
    """Create a GitHub branch.

    Args:
        base_ref: Base branch name.
        feature_ref: Feature branch name.

    Note:
        # TODO(team, 2024-05-22): Implement GitHub branch creation via GitHub App.
    """

    raise NotImplementedError("GitHub branch creation is not yet implemented.")


def apply_patch(diff: str) -> None:
    """Apply a unified diff to the GitHub repository.

    Args:
        diff: Unified diff text.

    Note:
        # TODO(team, 2024-05-22): Implement patch application using Git data APIs.
    """

    raise NotImplementedError("GitHub patch application is not yet implemented.")


def create_or_update_pr(*, title: str, body: str, head: str, base: str) -> int:
    """Create or update a pull request.

    Args:
        title: Pull request title.
        body: Pull request description.
        head: Head branch name.
        base: Base branch name.

    Returns:
        The pull request number.

    Note:
        # TODO(team, 2024-05-22): Implement PR upsert logic via GitHub GraphQL API.
    """

    raise NotImplementedError("GitHub PR integration is not yet implemented.")
