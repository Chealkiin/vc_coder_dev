"""Deterministic coder adapter used by the happy-path demo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from backend.agents.orchestrator.routing import CoderAdapter

_DEFAULT_DIFF_PATH = Path(__file__).resolve().parent / "diffs" / "demo_patch.txt"


@dataclass(frozen=True)
class DemoCoderResult:
    """Coder result payload returned by :class:`CoderAdapterFake`."""

    work_order_id: str
    diff: str
    notes: str

    def to_dict(self) -> Mapping[str, object]:
        """Return a mapping suitable for persistence."""

        return {"work_order_id": self.work_order_id, "diff": self.diff, "notes": self.notes}


class CoderAdapterFake(CoderAdapter):
    """Fake coder that returns a pre-computed unified diff."""

    def __init__(self, diff_path: Path | None = None) -> None:
        path = diff_path or _DEFAULT_DIFF_PATH
        self._diff_text = path.read_text(encoding="utf-8").strip()
        if not self._diff_text.startswith("diff --git "):
            raise ValueError("Demo diff must be a unified diff starting with 'diff --git '.")

    def build_coder_prompt(
        self, work_order: Mapping[str, object] | object, repo_meta: Mapping[str, object] | None = None
    ) -> str:
        """Return a deterministic prompt preview for debugging."""

        title = self._get_attr(work_order, "title", default="Demo Work Order")
        objective = self._get_attr(work_order, "objective", default="")
        return f"Implement: {title}\nObjective: {objective}"

    def execute(self, work_order: Mapping[str, object] | object) -> DemoCoderResult:
        """Return a deterministic diff for ``work_order``."""

        work_order_id = str(self._get_attr(work_order, "work_order_id", default="demo-work-order"))
        notes = "Applied canned diff for demo run"
        return DemoCoderResult(work_order_id=work_order_id, diff=self._diff_text, notes=notes)

    @staticmethod
    def _get_attr(work_order: Mapping[str, object] | object, key: str, *, default: object) -> object:
        """Retrieve ``key`` from ``work_order`` handling mappings and dataclasses."""

        if isinstance(work_order, Mapping):
            return work_order.get(key, default)
        return getattr(work_order, key, default)


__all__ = ["CoderAdapterFake", "DemoCoderResult"]
