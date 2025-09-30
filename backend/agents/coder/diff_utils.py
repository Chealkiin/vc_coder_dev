"""Utilities for working with unified diffs."""

from __future__ import annotations


def is_unified_diff(text: str) -> bool:
    """Return ``True`` when ``text`` looks like a ``diff --git`` payload."""

    if not text:
        return False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return stripped.startswith("diff --git ")
    return False


def summarize_unified_diff(text: str) -> dict[str, int]:
    """Return a light summary similar to ``git diff --numstat``."""

    changed_files: set[str] = set()
    additions = 0
    deletions = 0

    current_file: str | None = None

    for line in text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                current_file = parts[3][2:]
                changed_files.add(current_file)
            continue
        if line.startswith("+++"):
            if line.startswith("+++ b/"):
                current_file = line[6:]
                changed_files.add(current_file)
            continue
        if line.startswith("--- "):
            continue
        if line.startswith("@@"):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
            continue
        if line.startswith("-") and not line.startswith("---"):
            deletions += 1
            continue
        if line.startswith("new file mode") and current_file:
            changed_files.add(current_file)

    return {
        "changed_files": len(changed_files),
        "additions": additions,
        "deletions": deletions,
    }


def find_new_files(text: str) -> list[str]:
    """Return a list of repo-relative paths that are new in the diff."""

    new_files: list[str] = []
    pending_new: str | None = None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            pending_new = None
        if line.startswith("--- /dev/null"):
            pending_new = ""
            continue
        if line.startswith("+++ b/"):
            path = line[6:]
            if pending_new is not None:
                if path not in new_files:
                    new_files.append(path)
                pending_new = None
            continue
        if line.startswith("new file mode"):
            if pending_new and pending_new not in new_files:
                new_files.append(pending_new)
            pending_new = None
    return new_files
