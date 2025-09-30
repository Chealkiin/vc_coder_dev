"""Tests for contract normalization transforms."""

from __future__ import annotations

from core.contracts.transforms import DEFAULT_TRANSFORMS, Transform, apply_transforms


def test_work_order_default_transforms_applied() -> None:
    payload = {
        "depends_on": ["step-1"],
        "title": "  Implement feature  ",
        "objective": "Ship diff",
    }

    transformed, log = apply_transforms(payload, DEFAULT_TRANSFORMS["WorkOrder"])

    assert "depends_on" not in transformed
    assert transformed["dependencies"] == ["step-1"]
    assert transformed["title"] == "Implement feature"
    assert any(entry["rule"] == "rename_field" for entry in log)
    assert any(entry["rule"] == "strip_whitespace" for entry in log)


def test_clamp_list_transform() -> None:
    rules = [Transform(type="clamp_list_len", field="items", max_len=2)]
    payload = {"items": [1, 2, 3]}

    transformed, log = apply_transforms(payload, rules)

    assert transformed["items"] == [1, 2]
    assert log == [{"rule": "clamp_list_len", "field": "items", "max_len": 2}]

