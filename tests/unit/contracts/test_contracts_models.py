"""Tests for contract models."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from core.contracts import Issue, ValidationReport, WorkOrder
from core.contracts.version import DEFAULT_VERSION, SCHEMA_NS


def _work_order_payload() -> dict:
    return {
        "work_order_id": uuid4(),
        "title": "  Build feature  ",
        "objective": "  Ship clean diff  ",
        "constraints": ["no deps"],
        "acceptance_criteria": ["tests pass"],
        "context_files": ["README.md"],
        "return_format": "unified-diff",
    }


def test_work_order_rejects_extra_fields() -> None:
    payload = _work_order_payload()
    payload["unexpected"] = "nope"

    with pytest.raises(ValidationError):
        WorkOrder(**payload)


def test_work_order_serialization_and_schema_fields() -> None:
    work_order = WorkOrder(**_work_order_payload())

    assert work_order.schema_version == DEFAULT_VERSION
    assert work_order.schema_id == f"{SCHEMA_NS}/WorkOrder/{DEFAULT_VERSION}"

    serialized = work_order.to_dict()
    assert serialized["schema_version"] == DEFAULT_VERSION
    assert json.loads(work_order.to_json())["schema_id"] == work_order.schema_id

    schema = json.loads(WorkOrder.schema_json())
    assert schema["$id"].endswith(f"/WorkOrder/{DEFAULT_VERSION}")


def test_validation_report_nested_model() -> None:
    report = ValidationReport(
        step_id=uuid4(),
        fatal=[Issue(code="ERR", file="file.py", line=3, msg="boom")],
        warnings=[Issue(code="WARN", file=None, line=None, msg="careful")],
        metrics={"tests_run": 3},
    )

    assert report.fatal[0].code == "ERR"
    assert report.metrics["tests_run"] == 3

