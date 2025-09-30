"""Python validator integration executing Ruff and MyPy on demand."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass

from backend.agents.validator.report_model import FatalItem, WarningItem


@dataclass
class ValidatorOutput:
    """Container describing validator findings and metrics."""

    fatal: list[FatalItem]
    warnings: list[WarningItem]
    lint_errors: int = 0


def run_python_validators(paths: Sequence[str]) -> ValidatorOutput:
    """Execute Ruff and MyPy against the provided Python paths."""

    if not paths:
        return ValidatorOutput(fatal=[], warnings=[], lint_errors=0)

    fatal: list[FatalItem] = []
    warnings: list[WarningItem] = []

    fatal.extend(_run_ruff(paths))
    fatal.extend(_run_mypy(paths))

    return ValidatorOutput(fatal=fatal, warnings=warnings, lint_errors=len(fatal))


def _run_ruff(paths: Sequence[str]) -> list[FatalItem]:
    try:
        completed = subprocess.run(
            ["ruff", "check", "--output-format", "json", *paths],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:  # pragma: no cover - defensive
        return [
            FatalItem(
                code="PY_RUFF_MISSING",
                file="",
                line=None,
                msg=(
                    "ruff executable not found: install dependencies to enable linting."
                ),
            )
        ]

    if not completed.stdout.strip() and completed.returncode == 0:
        return []

    try:
        findings = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError:
        message = completed.stderr.strip() or "ruff produced invalid JSON output"
        return [
            FatalItem(
                code="PY_RUFF_ERROR",
                file="",
                line=None,
                msg=message,
            )
        ]

    fatal: list[FatalItem] = []
    for item in findings:
        fatal.append(
            FatalItem(
                code=item.get("code", "PY_RUFF"),
                file=item.get("filename", ""),
                line=item.get("location", {}).get("row"),
                msg=item.get("message", "Ruff reported a violation."),
            )
        )

    if completed.returncode not in (0, 1):
        fatal.append(
            FatalItem(
                code="PY_RUFF_ERROR",
                file="",
                line=None,
                msg=(
                    completed.stderr.strip()
                    or "ruff exited with an unexpected status."
                ),
            )
        )

    return fatal


def _run_mypy(paths: Sequence[str]) -> list[FatalItem]:
    try:
        completed = subprocess.run(
            ["mypy", "--strict", *paths],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:  # pragma: no cover - defensive
        return [
            FatalItem(
                code="PY_MYPY_MISSING",
                file="",
                line=None,
                msg=(
                    "mypy executable not found: install dependencies to enable type "
                    "checking."
                ),
            )
        ]

    if completed.returncode == 0:
        return []

    fatal: list[FatalItem] = []
    stdout_lines = completed.stdout.splitlines()
    for raw_line in stdout_lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("Found ") or stripped.startswith(
            "Success: "
        ):
            continue
        if ": error:" not in stripped:
            # Fallback for unexpected output while still surfacing context.
            fatal.append(
                FatalItem(
                    code="PY_MYPY",
                    file="",
                    line=None,
                    msg=stripped,
                )
            )
            continue

        prefix, message = stripped.split(": error:", maxsplit=1)
        parts = prefix.split(":")
        file_path = parts[0]
        line_number = None
        if len(parts) > 1 and parts[1].isdigit():
            line_number = int(parts[1])
        fatal.append(
            FatalItem(
                code="PY_MYPY",
                file=file_path,
                line=line_number,
                msg=message.strip(),
            )
        )

    if not fatal:
        fatal.append(
            FatalItem(
                code="PY_MYPY",
                file="",
                line=None,
                msg=(
                    completed.stderr.strip()
                    or "mypy failed without emitting diagnostics."
                ),
            )
        )

    return fatal


__all__ = ["ValidatorOutput", "run_python_validators"]
