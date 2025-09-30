"""Helpers for capturing lifecycle events inside demo workflows."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import IO, Iterable, List, Mapping, Sequence

from core.events.publisher import EventsPublisher
from core.events.types import LifecycleEvent


@dataclass(frozen=True)
class CapturedEvent:
    """Wrapper combining the canonical event and its serialized payload."""

    event: LifecycleEvent
    payload: Mapping[str, object]


class InMemoryEventsPublisher(EventsPublisher):
    """Event publisher that stores events and prints structured lines.

    The demo wiring relies on this publisher to provide human-friendly
    observability without requiring an external streaming service. Each
    published event is appended to :attr:`events` and emitted as a single
    JSON line on ``stdout`` (or the provided stream) so that the CLI can
    replay the lifecycle transitions in order.
    """

    def __init__(self, stream: IO[str] | None = None) -> None:
        self._stream: IO[str] = stream or sys.stdout
        self._events: List[CapturedEvent] = []

    @property
    def events(self) -> Sequence[CapturedEvent]:
        """Expose the captured events for assertions and summaries."""

        return list(self._events)

    def publish(self, event: LifecycleEvent) -> None:
        """Persist ``event`` and echo a JSON line for human consumption."""

        payload = self._serialise_event(event)
        self._events.append(CapturedEvent(event=event, payload=payload))
        json_record = json.dumps(payload, sort_keys=True)
        self._stream.write(json_record + "\n")
        self._stream.flush()

    def list_events(self, run_id: str | None = None) -> Sequence[LifecycleEvent]:
        """Return the published events filtered by ``run_id`` when provided."""

        if run_id is None:
            return [captured.event for captured in self._events]
        return [captured.event for captured in self._events if captured.event.run_id == run_id]

    def iter_payloads(self) -> Iterable[Mapping[str, object]]:
        """Yield the serialized payloads in the order they were published."""

        for captured in self._events:
            yield captured.payload

    def _serialise_event(self, event: LifecycleEvent) -> Mapping[str, object]:
        """Serialise ``event`` into a deterministic mapping for printing."""

        timestamp = event.timestamp if isinstance(event.timestamp, datetime) else datetime.fromisoformat(
            str(event.timestamp)
        )
        payload: dict[str, object] = {
            "ts": timestamp.isoformat(),
            "level": "info",
            "run_id": event.run_id,
            "step_id": event.step_id,
            "agent": "orchestrator",
            "phase": event.state,
            "message": event.event_type.value,
        }
        if event.duration_ms is not None:
            payload["duration_ms"] = event.duration_ms
        if event.meta is not None:
            payload["meta"] = dict(event.meta)
        return payload


__all__ = ["CapturedEvent", "InMemoryEventsPublisher"]
