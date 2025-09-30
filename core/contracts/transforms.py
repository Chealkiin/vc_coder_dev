"""Normalization transforms for contract payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Literal, Tuple


TransformType = Literal[
    "rename_field",
    "coerce_type",
    "default_if_missing",
    "strip_whitespace",
    "clamp_list_len",
]


@dataclass(frozen=True)
class Transform:
    """A normalization instruction applied to payload dictionaries."""

    type: TransformType
    from_field: str | None = None
    to_field: str | None = None
    field: str | None = None
    target_type: type | None = None
    default: Any = None
    max_len: int | None = None


def apply_transforms(payload: Dict[str, Any], rules: Iterable[Transform]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Apply normalization transforms to a payload dictionary."""

    transformed = dict(payload)
    log: List[Dict[str, Any]] = []

    for rule in rules:
        if rule.type == "rename_field":
            from_field = rule.from_field
            to_field = rule.to_field
            if not from_field or not to_field or from_field not in transformed:
                continue
            value = transformed.pop(from_field)
            if to_field not in transformed:
                transformed[to_field] = value
                log.append({"rule": "rename_field", "from": from_field, "to": to_field})
            else:
                transformed[to_field] = transformed[to_field]
        elif rule.type == "coerce_type":
            field = rule.field
            target_type = rule.target_type
            if not field or target_type is None or field not in transformed:
                continue
            value = transformed[field]
            try:
                transformed[field] = target_type(value)
                log.append({"rule": "coerce_type", "field": field, "type": target_type.__name__})
            except (TypeError, ValueError):
                log.append({"rule": "coerce_type", "field": field, "type": target_type.__name__, "error": "conversion_failed"})
        elif rule.type == "default_if_missing":
            field = rule.field
            if not field or field in transformed:
                continue
            transformed[field] = rule.default
            log.append({"rule": "default_if_missing", "field": field, "value": rule.default})
        elif rule.type == "strip_whitespace":
            field = rule.field
            if not field or field not in transformed:
                continue
            value = transformed[field]
            if isinstance(value, str):
                stripped = value.strip()
                if stripped != value:
                    transformed[field] = stripped
                    log.append({"rule": "strip_whitespace", "field": field})
        elif rule.type == "clamp_list_len":
            field = rule.field
            max_len = rule.max_len
            if not field or max_len is None or field not in transformed:
                continue
            value = transformed[field]
            if isinstance(value, list) and len(value) > max_len:
                transformed[field] = value[:max_len]
                log.append({"rule": "clamp_list_len", "field": field, "max_len": max_len})

    return transformed, log


DEFAULT_TRANSFORMS: Dict[str, List[Transform]] = {
    "WorkOrder": [
        Transform(type="rename_field", from_field="depends_on", to_field="dependencies"),
        Transform(type="strip_whitespace", field="title"),
        Transform(type="strip_whitespace", field="objective"),
    ],
    "CoderResult": [],
    "ValidationReport": [],
    "StepStatusPayload": [],
}

