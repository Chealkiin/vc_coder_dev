from __future__ import annotations

import json
import uuid

from backend.agents.validator.report_model import (
    FatalItem,
    ValidationReport,
    WarningItem,
)


def test_validation_report_serialization_and_schema():
    step_id = uuid.uuid4()
    report = ValidationReport(
        step_id=step_id,
        fatal=[
            FatalItem(
                code="PY_RUFF",
                file="backend/foo.py",
                line=12,
                msg="Unused import.",
            )
        ],
        warnings=[
            WarningItem(
                code="JS_ESLINT",
                file="frontend/app.tsx",
                msg="Console statement detected.",
            )
        ],
    )

    payload = report.model_dump()
    assert payload["step_id"] == step_id
    assert payload["fatal"][0]["code"] == "PY_RUFF"
    assert payload["warnings"][0]["file"] == "frontend/app.tsx"

    json_payload = json.dumps(report.model_dump(mode="json"))
    assert "Unused import" in json_payload

    schema = report.model_json_schema()
    assert "fatal" in schema["properties"]
    fatal_schema = schema["properties"]["fatal"]
    assert fatal_schema["type"] == "array"
    fatal_def = schema["$defs"]["FatalItem"]
    assert fatal_def["properties"]["code"]["type"] == "string"
