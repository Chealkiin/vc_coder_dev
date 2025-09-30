"""Policy helpers controlling orchestrator behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Sequence


@dataclass(frozen=True)
class MergeDecision:
    """Decision returned by :class:`MergePolicy`."""

    action: str
    reason: str | None = None

    def to_mapping(self) -> MutableMapping[str, str | None]:
        """Return a serialisable representation of the decision."""

        return {"action": self.action, "reason": self.reason}


class MergePolicy:
    """Evaluate whether the orchestrator should attempt an automatic merge."""

    def evaluate(
        self,
        config: Mapping[str, object],
        report: Mapping[str, object] | object,
        step_meta: Mapping[str, object] | None = None,
    ) -> MergeDecision:
        """Return a merge decision based on configuration and validation results."""

        fatal_items = self._extract_sequence(report, "fatal")
        if fatal_items:
            return MergeDecision(action="blocked", reason="fatal_validation")

        merge_cfg = config.get("merge") if isinstance(config, Mapping) else None
        auto_enabled = False
        if isinstance(merge_cfg, Mapping):
            auto_enabled = bool(merge_cfg.get("auto"))

        if auto_enabled:
            return MergeDecision(action="auto")

        return MergeDecision(action="manual")

    @staticmethod
    def _extract_sequence(report: Mapping[str, object] | object, key: str) -> Sequence[object]:
        if isinstance(report, Mapping):
            value = report.get(key, [])
        else:
            value = getattr(report, key, [])
        if isinstance(value, Sequence):
            return value
        return []


DEFAULT_MERGE_POLICY = MergePolicy()
