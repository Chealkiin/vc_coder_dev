"""Deterministic GitHub client fake for the happy-path demo."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping, Tuple

from backend.agents.github.github_client import validate_branch_name, validate_unified_diff
from backend.agents.orchestrator.routing import GitHubClient

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DryRunPatchSummary:
    """Patch summary that mirrors :class:`PatchSummary` for coercion."""

    changed_files: int
    additions: int
    deletions: int

    def to_dict(self) -> Mapping[str, object]:
        """Return a mapping representation for persistence."""

        return {
            "changed_files": self.changed_files,
            "additions": self.additions,
            "deletions": self.deletions,
        }


class GitHubClientFake(GitHubClient):
    """GitHub client fake that records intentions without network access."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or LOGGER
        self.ensure_calls: list[Tuple[str, str]] = []
        self.patch_calls: list[Tuple[str, str]] = []
        self.pr_calls: list[Tuple[str, str, str, str]] = []
        self.update_calls: list[Tuple[int, str]] = []
        self.comment_calls: list[Tuple[int, str]] = []

    def ensure_branch(self, base_ref: str, feature_ref: str) -> None:
        """Record an intent to ensure the feature branch exists."""

        validate_branch_name(base_ref)
        validate_branch_name(feature_ref)
        self.ensure_calls.append((base_ref, feature_ref))
        self._logger.info("github.ensure_branch", extra={"base_ref": base_ref, "feature_ref": feature_ref})

    def apply_patch(self, feature_ref: str, unified_diff: str) -> DryRunPatchSummary:
        """Validate the diff and return a deterministic patch summary."""

        validate_branch_name(feature_ref)
        validate_unified_diff(unified_diff)
        self.patch_calls.append((feature_ref, unified_diff))
        additions = self._count_lines(unified_diff, prefix="+")
        deletions = self._count_lines(unified_diff, prefix="-")
        summary = DryRunPatchSummary(changed_files=1, additions=additions, deletions=deletions)
        self._logger.info(
            "github.apply_patch",
            extra={"feature_ref": feature_ref, "additions": additions, "deletions": deletions},
        )
        return summary

    def create_or_update_pr(self, title: str, body_md: str, head: str, base: str) -> Tuple[int, str]:
        """Return a canned PR identifier without performing network calls."""

        validate_branch_name(head)
        validate_branch_name(base)
        self.pr_calls.append((title, body_md, head, base))
        self._logger.info(
            "github.create_pr",
            extra={"title": title, "head": head, "base": base, "body_length": len(body_md)},
        )
        return 123, "https://example.test/pr/123"

    def update_pr_body(self, pr_number: int, body_md: str) -> None:
        """Record body updates for observability in tests and demo output."""

        self.update_calls.append((pr_number, body_md))
        self._logger.info(
            "github.update_pr_body", extra={"pr_number": pr_number, "body_length": len(body_md)}
        )

    def post_comment(self, pr_number: int, body_md: str) -> None:
        """Record pull request comments for completeness."""

        self.comment_calls.append((pr_number, body_md))
        self._logger.info(
            "github.post_comment", extra={"pr_number": pr_number, "body_length": len(body_md)}
        )

    def _count_lines(self, diff: str, *, prefix: str) -> int:
        """Count diff lines beginning with ``prefix`` excluding headers."""

        total = 0
        for line in diff.splitlines():
            if not line or line.startswith("diff --git "):
                continue
            if prefix == "+" and line.startswith("+++"):
                continue
            if prefix == "-" and line.startswith("---"):
                continue
            if line.startswith(prefix):
                total += 1
        return total


__all__ = ["DryRunPatchSummary", "GitHubClientFake"]
