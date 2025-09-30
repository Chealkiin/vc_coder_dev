"""JavaScript and TypeScript validators (ESLint + tsc)."""

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


def run_js_validators(paths: Sequence[str]) -> ValidatorOutput:
    """Execute ESLint and TypeScript compiler checks for the given files."""

    if not paths:
        return ValidatorOutput(fatal=[], warnings=[], lint_errors=0)

    fatal: list[FatalItem] = []
    warnings: list[WarningItem] = []

    eslint_result = _run_eslint(paths)
    fatal.extend(eslint_result.fatal)
    warnings.extend(eslint_result.warnings)

    tsc_fatal = _run_tsc()
    fatal.extend(tsc_fatal)

    lint_errors = len(fatal)

    return ValidatorOutput(fatal=fatal, warnings=warnings, lint_errors=lint_errors)


@dataclass
class _ESLintResult:
    fatal: list[FatalItem]
    warnings: list[WarningItem]


def _run_eslint(paths: Sequence[str]) -> _ESLintResult:
    try:
        completed = subprocess.run(
            ["eslint", "--format", "json", "--max-warnings", "0", *paths],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:  # pragma: no cover - defensive
        fatal = [
            FatalItem(
                code="JS_ESLINT_MISSING",
                file="",
                line=None,
                msg=(
                    "eslint executable not found: install JavaScript tooling "
                    "to enable linting."
                ),
            )
        ]
        return _ESLintResult(fatal=fatal, warnings=[])

    stdout = completed.stdout.strip()
    if not stdout and completed.returncode == 0:
        return _ESLintResult(fatal=[], warnings=[])

    try:
        payload = json.loads(stdout or "[]")
    except json.JSONDecodeError:
        fatal = [
            FatalItem(
                code="JS_ESLINT_ERROR",
                file="",
                line=None,
                msg=completed.stderr.strip() or "eslint produced invalid JSON output.",
            )
        ]
        return _ESLintResult(fatal=fatal, warnings=[])

    fatal: list[FatalItem] = []
    warnings: list[WarningItem] = []

    for file_result in payload:
        file_path = file_result.get("filePath", "")
        for message in file_result.get("messages", []):
            severity = message.get("severity", 2)
            code = message.get("ruleId") or "JS_ESLINT"
            text = message.get("message", "ESLint reported an issue.")
            line_number = message.get("line")
            if severity == 2:
                fatal.append(
                    FatalItem(
                        code=code,
                        file=file_path,
                        line=line_number,
                        msg=text,
                    )
                )
            else:
                warnings.append(
                    WarningItem(
                        code=code,
                        file=file_path,
                        msg=text,
                    )
                )

    if completed.returncode not in (0, 1):
        fatal.append(
            FatalItem(
                code="JS_ESLINT_ERROR",
                file="",
                line=None,
                msg=(
                    completed.stderr.strip()
                    or "eslint exited with an unexpected status."
                ),
            )
        )

    return _ESLintResult(fatal=fatal, warnings=warnings)


def _run_tsc() -> list[FatalItem]:
    try:
        completed = subprocess.run(
            ["tsc", "--noEmit"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:  # pragma: no cover - defensive
        return [
            FatalItem(
                code="JS_TSC_MISSING",
                file="",
                line=None,
                msg=(
                    "tsc executable not found: install TypeScript tooling "
                    "to enable type checking."
                ),
            )
        ]

    if completed.returncode == 0:
        return []

    fatal: list[FatalItem] = []
    stdout_lines = completed.stdout.splitlines()
    for line in stdout_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if " error " not in stripped:
            fatal.append(
                FatalItem(
                    code="JS_TSC",
                    file="",
                    line=None,
                    msg=stripped,
                )
            )
            continue
        # Typical TypeScript output: path.ts(x)(line,col): error TS1234: message
        prefix, message = stripped.split(": error", maxsplit=1)
        file_part = prefix
        line_number = None
        if "(" in file_part and ")" in file_part:
            path_part, remainder = file_part.split("(", maxsplit=1)
            coordinates = remainder.rstrip(")")
            if "," in coordinates:
                line_text, _ = coordinates.split(",", maxsplit=1)
                if line_text.isdigit():
                    line_number = int(line_text)
            file_part = path_part
        fatal.append(
            FatalItem(
                code="JS_TSC",
                file=file_part,
                line=line_number,
                msg="error" + message,
            )
        )

    if not fatal:
        fatal.append(
            FatalItem(
                code="JS_TSC",
                file="",
                line=None,
                msg=(
                    completed.stderr.strip()
                    or "tsc failed without emitting diagnostics."
                ),
            )
        )

    return fatal


__all__ = ["ValidatorOutput", "run_js_validators"]
