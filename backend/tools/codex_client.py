"""Codex client stub for executing code generation prompts."""

from __future__ import annotations


def run(prompt: str) -> str:
    """Execute a prompt against the Codex backend.

    Args:
        prompt: Prompt text to execute.

    Returns:
        Unified diff text in `diff --git` format.

    Note:
        # TODO(team, 2024-05-22): Implement Codex API invocation with deterministic prompts.
    """

    raise NotImplementedError("Codex client integration is pending.")
