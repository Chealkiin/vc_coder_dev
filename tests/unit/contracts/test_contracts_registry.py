"""Tests for the contract registry."""

from __future__ import annotations

import pytest

from core.contracts import BaseContract, registry
from core.contracts.registry import register_contract
from core.contracts.version import DEFAULT_VERSION


def test_registry_lookup_by_name_and_alias() -> None:
    work_order_cls = registry.get("WorkOrder")
    assert issubclass(work_order_cls, BaseContract)

    from_alias = registry.get("work_order")
    assert from_alias is work_order_cls


def test_registry_unknown_contract_raises() -> None:
    with pytest.raises(KeyError):
        registry.get("unknown_contract")


def test_registry_registers_new_contract_with_alias() -> None:

    @register_contract(name="DemoContract", aliases=["demo"])
    class DemoContract(BaseContract):
        value: str

    retrieved = registry.get("DemoContract", version=DEFAULT_VERSION)
    assert retrieved is DemoContract

    alias_lookup = registry.get("demo")
    assert alias_lookup is DemoContract

