"""Tests for the GitHub client interface skeleton."""
from backend.agents.github.github_client import (
    GitHubClient,
    PatchSummary,
    validate_branch_name,
    validate_unified_diff,
)

import pytest


def test_client_methods_execute_in_dry_run() -> None:
    client = GitHubClient()
    client.ensure_branch("main", "feat/bootstrap")
    summary = client.apply_patch("feat/bootstrap", "diff --git a/file b/file")
    assert isinstance(summary, PatchSummary)
    assert summary == PatchSummary(changed_files=0, additions=0, deletions=0)

    pr_number, pr_url = client.create_or_update_pr(
        title="Bootstrap",
        body_md="body",
        head="feat/bootstrap",
        base="main",
    )
    assert pr_number == 0
    assert pr_url.endswith("/pull/0")

    client.update_pr_body(pr_number=0, body_md="updated body")
    client.post_comment(pr_number=0, body_md="comment")


def test_branch_validation_rejects_unsafe_names() -> None:
    validate_branch_name("feat/valid-branch")
    with pytest.raises(ValueError):
        validate_branch_name("invalid branch name")
    with pytest.raises(ValueError):
        validate_branch_name("../etc/passwd")


def test_unified_diff_validation() -> None:
    validate_unified_diff("diff --git a/file b/file")
    with pytest.raises(ValueError):
        validate_unified_diff("--- invalid diff")
