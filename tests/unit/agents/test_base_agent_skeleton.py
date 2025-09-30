"""Unit tests for the base agent scaffolding."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Mapping

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.agents.shared.base_agent import BaseAgent, StoreProtocol
from core.events import NoOpEventsPublisher


class DummyStore(StoreProtocol):
    """Bare bones store implementation for tests."""

    def __init__(self) -> None:
        self.run_repo = object()
        self.step_repo = object()
        self.artifact_repo = object()
        self.validation_report_repo = object()
        self.pr_binding_repo = object()


class DummyAgent(BaseAgent):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(
            store=DummyStore(),
            github_client=object(),
            logger=logger,
            events_publisher=NoOpEventsPublisher(),
            config={"feature": "on"},
        )
        self.prepare_called = False
        self.context_built: Mapping[str, object] | None = None

    def prepare(self, run_id: str, step_id: str | None = None) -> None:
        self.prepare_called = True

    def build_context(self, run_id: str, step_id: str | None = None) -> Mapping[str, object]:
        context = {"run": run_id, "step": step_id}
        self.context_built = context
        return context

    def execute(self, context: Mapping[str, object]) -> Mapping[str, object]:
        return {"executed": True, "context": context}


def test_base_agent_runs_lifecycle() -> None:
    stream = logging.StreamHandler()
    logger = logging.getLogger("dummy-agent")
    logger.setLevel(logging.DEBUG)
    logger.handlers = [stream]

    agent = DummyAgent(logger)
    result = agent.run("run-1", "step-1")

    assert agent.prepare_called is True
    assert agent.context_built == {"run": "run-1", "step": "step-1"}
    assert result["executed"] is True
    assert agent.config["feature"] == "on"

