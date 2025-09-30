"""GitHub client stub for repository operations."""

from __future__ import annotations


def create_branch(base: str, feature: str) -> None:
    """Create a new branch on GitHub.

    Note:
        # TODO(team, 2024-05-22): Implement GitHub branch creation using the GitHub App API.
    """

    raise NotImplementedError("GitHub client branch creation is pending.")


def apply_patch(diff: str) -> None:
    """Apply a unified diff to the repository.

    Note:
        # TODO(team, 2024-05-22): Implement diff application using the GitHub Checks API.
    """

    raise NotImplementedError("GitHub client patch application is pending.")


def create_or_update_pr(*, title: str, body: str, head: str, base: str) -> int:
    """Create or update a pull request on GitHub.

    Note:
        # TODO(team, 2024-05-22): Implement pull request upsert workflow via GraphQL.
    """

    raise NotImplementedError("GitHub client PR management is pending.")
