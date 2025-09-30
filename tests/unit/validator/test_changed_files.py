from __future__ import annotations

from collections.abc import Sequence
from unittest import mock

import pytest

from tools import changed_files


class _CompletedProcess:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout


@pytest.mark.parametrize(
    "numstat_output,new_files_output,expected",
    [
        (
            "10\t2\tbackend/foo.py\n5\t5\tbackend/bar.py\n0\t0\tfrontend/app.tsx",
            "backend/bar.py\nfrontend/app.tsx",
            {
                "backend/foo.py": (10, 2, False),
                "backend/bar.py": (5, 5, True),
                "frontend/app.tsx": (0, 0, True),
            },
        ),
    ],
)
def test_changed_files_git_stats(numstat_output, new_files_output, expected):
    command_outputs = {
        ("git", "diff", "--numstat", "origin/main...HEAD"): numstat_output,
        (
            "git",
            "diff",
            "--name-only",
            "--diff-filter=A",
            "origin/main...HEAD",
        ): new_files_output,
    }

    def fake_run(command: Sequence[str], capture_output: bool, text: bool, check: bool):
        key = tuple(command)
        return _CompletedProcess(stdout=command_outputs[key])

    with mock.patch.object(changed_files, "subprocess") as subprocess_mock:
        subprocess_mock.run.side_effect = fake_run
        files = changed_files.list_changed_files("origin/main")

    assert {file.path for file in files} == set(expected)
    for file in files:
        additions, deletions, is_new = expected[file.path]
        assert file.additions == additions
        assert file.deletions == deletions
        assert file.is_new_file is is_new


def test_summarize_changed_files_counts_lines_and_new_files():
    files = [
        changed_files.ChangedFile(
            path="a.py", additions=3, deletions=1, is_new_file=True
        ),
        changed_files.ChangedFile(
            path="b.ts", additions=2, deletions=2, is_new_file=False
        ),
    ]

    summary = changed_files.summarize_changed_files(files)

    assert summary.total_changed_lines == 8
    assert summary.new_files_count == 1
