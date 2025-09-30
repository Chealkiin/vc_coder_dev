"""HTTP server entrypoint for agent run orchestration."""

from __future__ import annotations

from typing import Any, Dict

from backend.core.logging import get_logger

logger = get_logger(__name__)


def create_app() -> Any:
    """Create the HTTP application server.

    Returns:
        The web application instance compatible with the chosen framework.

    Note:
        # TODO(team, 2024-05-22): Implement actual web framework integration.
    """

    raise NotImplementedError("Application server creation is not yet implemented.")


def register_routes(app: Any) -> None:
    """Register HTTP routes on the application.

    Args:
        app: The HTTP application instance.

    Note:
        # TODO(team, 2024-05-22): Define API routes for orchestrating runs.
    """

    raise NotImplementedError("Route registration is not yet implemented.")


def run_server(settings: Dict[str, Any]) -> None:
    """Run the HTTP server using the provided settings.

    Args:
        settings: Runtime configuration settings.

    Note:
        # TODO(team, 2024-05-22): Wire configuration, logging, and graceful shutdown.
    """

    logger.info("server.start", extra={"meta": {"settings_keys": list(settings.keys())}})
    raise NotImplementedError("Server execution is not yet implemented.")
