"""Base agent skeleton providing dependency injection and lifecycle orchestration."""

from __future__ import annotations

import logging
from typing import Mapping, Protocol

from backend.agents.shared.lifecycle_mixin import LifecycleMixin
from backend.agents.shared.logging_mixin import LoggingMixin
from core.events import EventsPublisher


class StoreProtocol(Protocol):
    """Protocol describing the repositories available to agents."""

    run_repo: object
    step_repo: object
    artifact_repo: object
    validation_report_repo: object
    pr_binding_repo: object


class BaseAgent(LifecycleMixin, LoggingMixin):
    """Provides a common lifecycle contract and dependency injection for agents."""

    def __init__(
        self,
        *,
        store: StoreProtocol,
        github_client: object,
        logger: logging.Logger,
        events_publisher: EventsPublisher,
        config: Mapping[str, object] | None = None,
    ) -> None:
        """Initialize the agent with production dependencies.

        Args:
            store: Aggregation of persistence repositories.
            github_client: Client responsible for GitHub interactions.
            logger: Destination for structured log events.
            events_publisher: Publisher used for lifecycle event emission.
            config: Optional configuration overrides for the agent.
        """

        self._store = store
        self._github_client = github_client
        self.logger = logger
        self._events_publisher = events_publisher
        self._config = dict(config or {})
        self.agent_name = self.__class__.__name__

    @property
    def config(self) -> Mapping[str, object]:
        """Return the immutable view of the agent configuration."""

        return self._config

    def run(self, run_id: str, step_id: str | None = None) -> Mapping[str, object]:
        """Execute the agent lifecycle in a deterministic order.

        Args:
            run_id: Identifier of the run being processed.
            step_id: Optional identifier of the step.

        Returns:
            Mapping containing the postprocessed result of the lifecycle.
        """

        self.log_json(logging.DEBUG, "prepare", run_id=run_id, step_id=step_id, phase="prepare")
        self.prepare(run_id, step_id)

        self.log_json(logging.DEBUG, "build_context", run_id=run_id, step_id=step_id, phase="build_context")
        context = self.build_context(run_id, step_id)

        self.log_json(logging.DEBUG, "execute", run_id=run_id, step_id=step_id, phase="execute")
        result = self.execute(context)

        self.log_json(logging.DEBUG, "postprocess", run_id=run_id, step_id=step_id, phase="postprocess")
        return self.postprocess(context, result)

