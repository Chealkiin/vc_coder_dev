"""Base contract definitions for Pydantic models."""

from __future__ import annotations

import json
from typing import Any, ClassVar, Dict

from pydantic import BaseModel, ConfigDict, Field

from .version import DEFAULT_VERSION, SCHEMA_NS


class ModelVersion:
    """Helpers for contract schema identifiers."""

    @staticmethod
    def make_schema_id(name: str, version: str) -> str:
        """Return a schema identifier for the given contract name and version."""

        return f"{SCHEMA_NS}/{name}/{version}"


class BaseContract(BaseModel):
    """Base class for all contract models."""

    model_config = ConfigDict(extra="forbid", frozen=False, ser_json_inf_nan='null')

    schema_version: str = Field(default="")
    schema_id: str = Field(default="")

    __contract_name__: ClassVar[str | None] = None
    __contract_version__: ClassVar[str] = DEFAULT_VERSION

    def model_post_init(self, __context: Any) -> None:
        schema_version = self.schema_version or self.contract_version()
        schema_id = self.schema_id or self.default_schema_id()
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "schema_id", schema_id)

    @classmethod
    def contract_name(cls) -> str:
        """Return the canonical contract name."""

        name = getattr(cls, "__contract_name__", None)
        return name or cls.__name__

    @classmethod
    def contract_version(cls) -> str:
        """Return the contract version."""

        return getattr(cls, "__contract_version__", DEFAULT_VERSION)

    @classmethod
    def default_schema_id(cls) -> str:
        """Return the default schema identifier for the contract."""

        return ModelVersion.make_schema_id(cls.contract_name(), cls.contract_version())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the model to a Python dictionary."""

        return self.model_dump(mode="python")

    def to_json(self) -> str:
        """Serialize the model to JSON."""

        return self.model_dump_json()

    @classmethod
    def model_json_schema(cls, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Return the JSON schema for the model with an injected identifier."""

        schema = super().model_json_schema(*args, **kwargs)
        schema.setdefault("$id", cls.default_schema_id())
        return schema

    @classmethod
    def schema_json(cls) -> str:
        """Return the JSON schema for the model."""

        return json.dumps(cls.model_json_schema(), sort_keys=True)

