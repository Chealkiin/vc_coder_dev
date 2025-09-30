"""Serialization helpers for orchestrator artifacts."""

from __future__ import annotations

from typing import Mapping

from core.store.repositories import ArtifactRepo, ValidationReportRepo


def persist_diff_artifact(
    artifact_repo: ArtifactRepo,
    *,
    run_id: str,
    step_id: str,
    diff: str,
) -> None:
    """Persist the unified diff returned by the coder."""

    artifact_repo.add(run_id=run_id, step_id=step_id, kind="diff", content=diff, meta={"bytes": len(diff)})


def persist_notes_artifact(
    artifact_repo: ArtifactRepo,
    *,
    run_id: str,
    step_id: str,
    notes: str | None,
) -> None:
    """Persist coder notes or planning logs when available."""

    if notes:
        artifact_repo.add(run_id=run_id, step_id=step_id, kind="doc", content=notes, meta={"category": "notes"})


def persist_patch_summary(
    artifact_repo: ArtifactRepo,
    *,
    run_id: str,
    step_id: str,
    summary: Mapping[str, object],
) -> None:
    """Persist the patch summary returned by the GitHub client."""

    artifact_repo.add(
        run_id=run_id,
        step_id=step_id,
        kind="doc",
        content="patch-summary",
        meta={"summary": dict(summary)},
    )


def persist_validation_report(
    report_repo: ValidationReportRepo,
    *,
    run_id: str,
    step_id: str,
    report: Mapping[str, object],
) -> None:
    """Persist the validation report for a step."""

    report_repo.add(run_id=run_id, step_id=step_id, report=report)
