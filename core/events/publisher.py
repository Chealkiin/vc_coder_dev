"""Event publisher interfaces used by the agent orchestration stack."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.events.types import LifecycleEvent


class EventsPublisher(ABC):
    """Abstract publisher responsible for delivering lifecycle events."""

    @abstractmethod
    def publish(self, event: LifecycleEvent) -> None:
        """Publish an event.

        Args:
            event: Event payload describing the lifecycle transition.
        """


class NoOpEventsPublisher(EventsPublisher):
    """Publisher that intentionally drops all events.

    This implementation allows unit tests and offline workflows to instantiate the
    orchestrator without configuring infrastructure dependencies.
    """

    def publish(self, event: LifecycleEvent) -> None:  # pragma: no cover - intentionally empty
        """Drop the event without any side effects."""

