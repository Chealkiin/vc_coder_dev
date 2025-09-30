"""Deterministic renderers for GitHub pull request bodies."""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence


def _format_metrics(metrics: Mapping[str, object]) -> Iterable[str]:
    for key, value in metrics.items():
        yield f"- {key}: {value}"


def render_pr_body(
    run_id: str,
    steps_summary: Sequence[str],
    validation_summary: str,
    metrics: Mapping[str, object],
) -> str:
    """Render the full pull request body used by the orchestrator."""

    lines: list[str] = ["## Summary", f"- Run ID: `{run_id}`"]
    if steps_summary:
        lines.extend(f"- {item}" for item in steps_summary)

    lines.extend(["", "## Changes"])
    if steps_summary:
        lines.extend(f"- {item}" for item in steps_summary)
    else:
        lines.append("- Pending step execution")

    lines.extend(["", "## Validation", validation_summary or "Pending validation results."])

    lines.extend(["", "## Metrics"])
    if metrics:
        lines.extend(_format_metrics(metrics))
    else:
        lines.append("- No metrics reported")

    lines.extend(["", "## Links", f"- Run: {run_id}", "- Artifacts: attached to run"])

    return "\n".join(lines)


def render_step_update(
    step_index: int,
    title: str,
    acceptance_criteria: Sequence[str],
    validator_results: Mapping[str, Mapping[str, object] | str],
) -> str:
    """Render a markdown snippet summarizing an individual step update."""

    lines: list[str] = [f"### Step {step_index}: {title}", "", "**Acceptance Criteria**"]
    if acceptance_criteria:
        lines.extend(f"- {item}" for item in acceptance_criteria)
    else:
        lines.append("- No acceptance criteria supplied")

    lines.extend(["", "**Validator Results**"])
    if validator_results:
        for name, result in validator_results.items():
            if isinstance(result, Mapping):
                status = result.get("status", "unknown")
                summary = result.get("summary")
                line = f"- {name}: {status}"
                if summary:
                    line += f" – {summary}"
            else:
                line = f"- {name}: {result}"
            lines.append(line)
    else:
        lines.append("- No validators executed")

    return "\n".join(lines)
