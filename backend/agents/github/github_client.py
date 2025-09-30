"""GitHub client interfaces for the agent runtime."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Tuple

from .errors import PatchApplyError

LOGGER = logging.getLogger(__name__)

BRANCH_NAME_PATTERN = re.compile(r"^(?!/)(?!.*//)(?!.*\.\.)[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")
DRY_RUN = True


@dataclass(slots=True)
class PatchSummary:
    """Summary describing the result of applying a patch."""

    changed_files: int
    additions: int
    deletions: int


def validate_unified_diff(diff: str) -> None:
    """Ensure the provided diff is a unified diff produced by git."""

    if not diff.startswith("diff --git "):
        raise ValueError("Unified diff must start with 'diff --git '.")


def validate_branch_name(name: str) -> None:
    """Validate a Git reference name for safety before using it remotely."""

    if not name:
        raise ValueError("Branch name must be provided.")
    if not BRANCH_NAME_PATTERN.match(name):
        raise ValueError("Branch name contains unsupported characters or structure.")


class GitHubClient:
    """Interface for GitHub operations required by the orchestrator."""

    def ensure_branch(self, base_ref: str, feature_ref: str) -> None:
        """Ensure ``feature_ref`` exists by creating it from ``base_ref`` if needed."""

        validate_branch_name(base_ref)
        validate_branch_name(feature_ref)
        LOGGER.info("ensure_branch", extra={"base_ref": base_ref, "feature_ref": feature_ref})
        if not DRY_RUN:
            raise NotImplementedError

    def apply_patch(self, feature_ref: str, unified_diff: str) -> PatchSummary:
        """Apply a unified diff onto ``feature_ref`` and return a summary."""

        validate_branch_name(feature_ref)
        validate_unified_diff(unified_diff)
        LOGGER.info("apply_patch", extra={"feature_ref": feature_ref})
        if DRY_RUN:
            # Deterministic placeholder summary until real integration is wired.
            return PatchSummary(changed_files=0, additions=0, deletions=0)
        raise PatchApplyError("Patch application not implemented.")

    def create_or_update_pr(self, title: str, body_md: str, head: str, base: str) -> Tuple[int, str]:
        """Create or update a pull request and return the PR number and URL."""

        validate_branch_name(head)
        validate_branch_name(base)
        LOGGER.info(
            "create_or_update_pr",
            extra={"title": title, "head": head, "base": base, "body_length": len(body_md)},
        )
        if DRY_RUN:
            return 0, "https://example.invalid/pull/0"
        raise NotImplementedError

    def update_pr_body(self, pr_number: int, body_md: str) -> None:
        """Update the body of an existing pull request."""

        LOGGER.info("update_pr_body", extra={"pr_number": pr_number, "body_length": len(body_md)})
        if not DRY_RUN:
            raise NotImplementedError

    def post_comment(self, pr_number: int, body_md: str) -> None:
        """Post a comment on a pull request."""

        LOGGER.info("post_comment", extra={"pr_number": pr_number, "body_length": len(body_md)})
        if not DRY_RUN:
            raise NotImplementedError
