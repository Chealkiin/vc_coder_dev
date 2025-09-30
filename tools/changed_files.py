"""Utilities for discovering changed files relative to a base reference."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.agents.validator.size_guards import DiffSummary


def _ensure_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _import_diff_summary():
    _ensure_repo_root()
    from backend.agents.validator.size_guards import DiffSummary

    return DiffSummary


@dataclass
class ChangedFile:
    """Represents a single file changed in the diff."""

    path: str
    additions: int
    deletions: int
    is_new_file: bool = False


def _run_git(command: Sequence[str]) -> str:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _diff_range(base_ref: str, head_ref: str = "HEAD") -> str:
    return f"{base_ref}...{head_ref}"


def list_changed_files(base_ref: str, head_ref: str = "HEAD") -> list[ChangedFile]:
    """Return metadata about files changed relative to the provided base ref."""

    diff_range = _diff_range(base_ref, head_ref)
    numstat_output = _run_git(["git", "diff", "--numstat", diff_range])
    new_files_output = _run_git(
        ["git", "diff", "--name-only", "--diff-filter=A", diff_range]
    )
    new_files = {line.strip() for line in new_files_output.splitlines() if line.strip()}

    changed: list[ChangedFile] = []
    for line in numstat_output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        additions_raw, deletions_raw, *path_parts = parts
        path = path_parts[-1]
        additions = int(additions_raw) if additions_raw.isdigit() else 0
        deletions = int(deletions_raw) if deletions_raw.isdigit() else 0
        changed.append(
            ChangedFile(
                path=path,
                additions=additions,
                deletions=deletions,
                is_new_file=path in new_files,
            )
        )

    return changed


def changed_file_paths(files: Iterable[ChangedFile]) -> list[str]:
    """Return just the file paths from a collection of :class:`ChangedFile`."""

    return [item.path for item in files]


def summarize_changed_files(files: Iterable[ChangedFile]) -> DiffSummary:
    """Aggregate diff stats for size guard evaluation."""

    diff_summary_cls = _import_diff_summary()
    total_lines = 0
    new_files_count = 0
    for item in files:
        total_lines += item.additions + item.deletions
        if item.is_new_file:
            new_files_count += 1
    return diff_summary_cls(
        total_changed_lines=total_lines, new_files_count=new_files_count
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List files changed against a base ref."
    )
    parser.add_argument(
        "--base-ref",
        required=True,
        help="Base git ref to diff against.",
    )
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head git ref to compare against (defaults to HEAD).",
    )
    args = parser.parse_args(argv)

    files = list_changed_files(args.base_ref, args.head_ref)
    for path in changed_file_paths(files):
        print(path)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
