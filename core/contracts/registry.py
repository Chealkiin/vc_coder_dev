"""Registry for contract models."""

from __future__ import annotations

from typing import Dict, Iterable, Sequence, Tuple, Type, TypeVar

from .base import BaseContract
from .version import DEFAULT_VERSION


ContractT = TypeVar("ContractT", bound=BaseContract)


class ContractRegistry:
    """In-memory registry for contract models."""

    def __init__(self) -> None:
        self._contracts: Dict[Tuple[str, str], Type[BaseContract]] = {}
        self._default_versions: Dict[str, str] = {}
        self._aliases: Dict[str, Tuple[str, str]] = {}

    def register(
        self,
        model_cls: Type[ContractT],
        *,
        name: str | None = None,
        version: str = DEFAULT_VERSION,
        aliases: Iterable[str] | None = None,
    ) -> Type[ContractT]:
        """Register a contract model and optional aliases."""

        contract_name = name or model_cls.contract_name()
        model_cls.__contract_name__ = contract_name
        model_cls.__contract_version__ = version

        key = (contract_name, version)
        if key in self._contracts and self._contracts[key] is not model_cls:
            raise ValueError(f"Contract already registered for {contract_name} v{version}")

        self._contracts[key] = model_cls
        self._default_versions.setdefault(contract_name, version)

        for alias in aliases or ():
            self._aliases[alias] = key

        self._aliases.setdefault(contract_name, key)
        return model_cls

    def get(self, name_or_alias: str, version: str | None = None) -> Type[BaseContract]:
        """Retrieve a registered contract by name or alias."""

        key = self._resolve_key(name_or_alias, version)
        try:
            return self._contracts[key]
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyError(f"Unknown contract: {name_or_alias} (v{key[1]})") from exc

    def items(self) -> Sequence[Tuple[Tuple[str, str], Type[BaseContract]]]:
        """Return the registered contract mappings."""

        return tuple(self._contracts.items())

    def _resolve_key(self, name_or_alias: str, version: str | None) -> Tuple[str, str]:
        if name_or_alias in self._aliases:
            alias_name, alias_version = self._aliases[name_or_alias]
            if version is None:
                return alias_name, alias_version
            return alias_name, version

        contract_name = name_or_alias
        resolved_version = version or self._default_versions.get(contract_name)
        if resolved_version is None:
            raise KeyError(f"No version registered for contract '{contract_name}'")
        return contract_name, resolved_version


registry = ContractRegistry()


def register_contract(
    *,
    name: str,
    version: str = DEFAULT_VERSION,
    aliases: Iterable[str] | None = None,
):
    """Decorator to register a contract class with the registry."""

    def decorator(model_cls: Type[ContractT]) -> Type[ContractT]:
        return registry.register(model_cls, name=name, version=version, aliases=aliases)

    return decorator

