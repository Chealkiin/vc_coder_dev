#!/usr/bin/env python3
"""Print JSON schemas for all registered contract models."""

from __future__ import annotations

import json

from core.contracts import registry


def main() -> None:
    contracts = sorted(registry.items(), key=lambda item: item[0])
    for (name, version), model_cls in contracts:
        schema = model_cls.model_json_schema()
        print(f"# {name} v{version}")
        print(json.dumps(schema, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

