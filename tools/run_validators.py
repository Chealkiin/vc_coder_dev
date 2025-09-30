"""CLI to run repository validators against changed files."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4


def _ensure_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _filter_paths(paths: Sequence[str], suffixes: Sequence[str]) -> list[str]:
    return [path for path in paths if Path(path).suffix in suffixes]


def main(argv: Sequence[str] | None = None) -> int:
    _ensure_repo_root()
    from backend.agents.validator.js_validator import run_js_validators
    from backend.agents.validator.python_validator import run_python_validators
    from backend.agents.validator.report_model import Metrics, ValidationReport
    from backend.agents.validator.size_guards import check_diff_size
    from tools.changed_files import (
        changed_file_paths,
        list_changed_files,
        summarize_changed_files,
    )

    parser = argparse.ArgumentParser(description="Run validators for changed files.")
    parser.add_argument(
        "--base-ref",
        required=True,
        help="Base git reference used to determine changed files.",
    )
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head git reference used to determine changed files (default: HEAD).",
    )
    args = parser.parse_args(argv)

    changed = list_changed_files(args.base_ref, args.head_ref)
    summary = summarize_changed_files(changed)

    report = ValidationReport(step_id=uuid4())

    size_guard_fatal = check_diff_size(summary)
    if size_guard_fatal:
        report.fatal.append(size_guard_fatal)
        report.metrics = Metrics(
            lint_errors=len(report.fatal),
            tests_run=0,
            tests_failed=0,
        )
        print(json.dumps(report.model_dump(mode="json"), indent=2))
        return 1

    paths = changed_file_paths(changed)
    python_files = _filter_paths(paths, (".py",))
    js_files = _filter_paths(paths, (".js", ".ts", ".tsx"))

    lint_errors = 0

    python_result = run_python_validators(python_files)
    report.fatal.extend(python_result.fatal)
    report.warnings.extend(python_result.warnings)
    lint_errors += python_result.lint_errors

    js_result = run_js_validators(js_files)
    report.fatal.extend(js_result.fatal)
    report.warnings.extend(js_result.warnings)
    lint_errors += js_result.lint_errors

    report.metrics = Metrics(lint_errors=lint_errors, tests_run=0, tests_failed=0)

    exit_code = 1 if report.has_fatal else 0

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return exit_code


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
