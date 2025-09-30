"""Tests validating lifecycle event serialization."""

from __future__ import annotations

from datetime import datetime, timezone

from core.events.types import (
    LifecycleEventType,
    RunStatusChanged,
    StepCommitted,
    StepPaused,
    StepPlanned,
)


def test_step_event_to_dict_contains_expected_fields() -> None:
    timestamp = datetime.now(timezone.utc)
    event = StepPlanned(
        run_id="run-1",
        step_id="step-1",
        state="planned",
        timestamp=timestamp,
        duration_ms=42,
        meta={"phase": "planned"},
    )

    payload = event.to_dict()

    assert payload["run_id"] == "run-1"
    assert payload["step_id"] == "step-1"
    assert payload["event_type"] == LifecycleEventType.STEP_PLANNED.value
    assert payload["duration_ms"] == 42
    assert payload["meta"] == {"phase": "planned"}


def test_run_status_event_serializes_without_step() -> None:
    event = RunStatusChanged(
        run_id="run-2",
        step_id=None,
        state="running",
        timestamp=datetime.now(timezone.utc),
        meta={"reason": "resume"},
    )

    payload = event.to_dict()

    assert payload["run_id"] == "run-2"
    assert payload["step_id"] is None
    assert payload["meta"] == {"reason": "resume"}


def test_step_event_type_property_matches_enum() -> None:
    event = StepCommitted(
        run_id="run-3",
        step_id="step-7",
        state="committing",
        timestamp=datetime.now(timezone.utc),
    )

    assert event.type == LifecycleEventType.STEP_COMMITTED


def test_step_event_handles_optional_meta() -> None:
    event = StepPaused(
        run_id="run-5",
        step_id="step-9",
        state="paused",
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        meta=None,
    )

    payload = event.to_dict()
    assert "meta" not in payload
