"""Schemas for rules TOML files."""

from typing import Literal

from pydantic import Field

from spf.schemas import StrictModel
from spf.schemas import type_aliases as t


class IntVariableConfig(StrictModel):
    type: Literal["int"]
    min: int | None = None
    max: int | None = None
    values: list[int] | None = None

    def validate(self, value: int) -> int:
        """Validate the given value."""
        if self.min is not None and value < self.min:
            msg = f"Value {value} less than minimum {self.min}"
            raise ValueError(msg)
        if self.max is not None and value > self.max:
            msg = f"Value {value} greater than maximum {self.max}"
            raise ValueError(msg)
        if self.values is not None and value not in self.values:
            msg = f"Value {value} not any of {self.values}"
            raise ValueError(msg)
        return value


class StringVariableConfig(StrictModel):
    type: Literal["str"]
    min: int | None = None
    max: int | None = None
    values: list[str] | None = None

    def validate(self, value: str) -> str:
        """Validate the given value."""
        if self.values is not None and value not in self.values:
            msg = f"Value {value} not any of {self.values}"
            raise ValueError(msg)
        return value


class SpecialRuleConfig(StrictModel):
    name: str
    short: str
    explanation: str
    example: str | None = None
    description: str | None = None
    token: str | None = None
    variables: dict[str, IntVariableConfig | StringVariableConfig] | None = None
    versions: dict[str, str] | None = None


class SpecialRulesConfig(StrictModel):
    assault: dict[str, SpecialRuleConfig]
    unit: dict[str, SpecialRuleConfig]
    weapon: dict[str, SpecialRuleConfig]


#
# Tokens
#
class TokenRuleConfig(StrictModel):
    name: str
    effect: str
    short: str | None = None
    phases: list[t.PhaseName] = Field(default_factory=list)
    remove: str | None = None
    variables: dict[str, IntVariableConfig | StringVariableConfig] | None = None


class TokenRulesConfig(StrictModel):
    tokens: dict[str, TokenRuleConfig]


#
# Hexes
#
class HexRuleConfig(StrictModel):
    name: str
    effect: str
    short: str | None = None
    phases: list[t.PhaseName] = Field(default_factory=list)
    remove: str | None = None
    variables: dict[str, IntVariableConfig | StringVariableConfig] | None = None


class HexRulesConfig(StrictModel):
    explanation: str
    hexes: dict[str, HexRuleConfig]
