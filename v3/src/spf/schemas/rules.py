"""Schemas for rules TOML files.

Every registry record shares one core — name, prose, variables, references —
and adds only the fields its own registry needs (ADR 0024). The shapes stay
hand-written pydantic: vocabulary validation moves to load time, but schema
checking is what makes the data safe to write.
"""

import re
from typing import Annotated, ClassVar, Literal, Self, TypeIs

from pydantic import Field, StringConstraints, model_validator

from spf.schemas import StrictModel
from spf.schemas import type_aliases as t

_REF_PATTERN = r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$"

type Ref = Annotated[str, StringConstraints(pattern=_REF_PATTERN)]
"""A reference into a registry, always `<namespace>.<id>`, always qualified.

One value type with one syntax, used identically as an argument, as an entry in
`places` / `see_also`, and as a version overlay's key. Resolving it against the
namespace registry is the loader's job; the shape is checked here.
"""

_DIE = re.compile(r"^d\d+$")


def _is_int(value: object) -> TypeIs[int]:
    """Whether a value is a number a rule can interpolate.

    `bool` subclasses `int` in Python, but `N = true` is no count, so a bool is
    not accepted anywhere an int is asked for.
    """
    return isinstance(value, int) and not isinstance(value, bool)


type Slot = Literal["unit", "model", "assault", "range"]
type Modifier = Literal["-2", "-1", "0", "+1", "+2", "+3", "-N", "+N"]
"""A to-hit modifier as authored — a signed string, not a number, because `-N`
stands for a value the rule itself supplies."""

type ScalarType = Literal["int", "str", "die", "formula"]


class _VariableConfig(StrictModel):
    """What every variable declaration carries, whatever its type."""

    optional: bool = False
    """Whether an instance may leave this variable out.

    An absent optional variable elides its own `[...]` group from the rendered
    signature, so the rule reads as though it were never declared.
    """


class IntVariableConfig(_VariableConfig):
    type: Literal["int"]
    min: int | None = None
    max: int | None = None
    values: list[int] | None = None

    def validate_value(self, value: int) -> int:
        """Validate the given value.

        The type is checked before the bounds: a variable declaring neither
        `min`, `max` nor `values` still constrains what may be written.
        """
        if not _is_int(value):
            msg = f"Value {value} is not an int"
            raise ValueError(msg)
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


class StringVariableConfig(_VariableConfig):
    type: Literal["str"]
    min: int | None = None
    max: int | None = None
    values: list[str] | None = None

    def validate_value(self, value: str) -> str:
        """Validate the given value, its type before its value set."""
        if not isinstance(value, str):
            # ValueError, not TypeError: every way a value can fail a variable
            # is one kind of answer to the caller, which reports them alike.
            msg = f"Value {value} is not a str"
            raise ValueError(msg)  # noqa: TRY004
        if self.values is not None and value not in self.values:
            msg = f"Value {value} not any of {self.values}"
            raise ValueError(msg)
        return value


class DieVariableConfig(_VariableConfig):
    """A variable whose value is a die rather than a number: `d6`, not `6`."""

    type: Literal["die"]

    def validate_value(self, value: str) -> str:
        """Validate the given value."""
        if not isinstance(value, str) or not _DIE.match(value):
            msg = f"Value {value} is not a die"
            raise ValueError(msg)
        return value


class FormulaVariableConfig(_VariableConfig):
    """A variable whose value is not known at authoring time: `X`, not `6`.

    Its value is prose standing in for a number the game supplies — "the power
    of the poison gas" — so there is nothing to check but that it was written.
    """

    type: Literal["formula"]

    def validate_value(self, value: str) -> str:
        """Validate the given value."""
        if not isinstance(value, str) or not value:
            msg = f"Value {value} is not a formula"
            raise ValueError(msg)
        return value


class RefVariableConfig(_VariableConfig):
    """A variable whose value is a reference into one or more namespaces.

    The namespace *is* the value set: every member of it is legal. `values`
    narrows that to a subset, and is the exception — a hand-maintained list is
    what rots.
    """

    type: Literal["ref"]
    namespaces: list[str] = Field(min_length=1)
    values: list[Ref] | None = None


class UnionVariableConfig(_VariableConfig):
    """A variable authored as either of several scalar types: `6` or `d6`."""

    type: list[ScalarType] = Field(min_length=2)
    min: int | None = None
    max: int | None = None
    values: list[int | str] | None = None

    def validate_value(self, value: int | str) -> int | str:
        """Validate the given value against whichever member type it matches.

        The bounds constrain the numeric member only: a die is not a number,
        so `d20` is out of no range.
        """
        if _is_int(value) and "int" in self.type:
            return IntVariableConfig(
                type="int", min=self.min, max=self.max
            ).validate_value(self._check_values(value))
        if isinstance(value, str) and "die" in self.type and _DIE.match(value):
            return self._check_values(value)
        if isinstance(value, str) and "str" in self.type:
            return self._check_values(value)
        if isinstance(value, str) and "formula" in self.type and value:
            # A formula is the value the author could not know, so no value set
            # can enumerate it: the subset constrains the union's other members.
            return value
        msg = f"Value {value} is not {_or_list(self.type)}"
        raise ValueError(msg)

    def _check_values[T: (int, str)](self, value: T) -> T:
        """Check the value against the explicit subset, when one is declared."""
        if self.values is not None and value not in self.values:
            msg = f"Value {value} not any of {self.values}"
            raise ValueError(msg)
        return value


def _or_list(types: list[ScalarType]) -> str:
    """Spell a union of scalar types as English: `an int or a die`."""
    worded = [f"{'an' if scalar.startswith('i') else 'a'} {scalar}" for scalar in types]
    return f"{', '.join(worded[:-1])} or {worded[-1]}"


type ScalarVariableConfig = (
    IntVariableConfig
    | StringVariableConfig
    | DieVariableConfig
    | FormulaVariableConfig
    | UnionVariableConfig
)
"""A variable whose value is written out, rather than pointed at."""

type VariableConfig = ScalarVariableConfig | RefVariableConfig


class RuleRecord(StrictModel):
    """What every registry record carries, whatever registry it belongs to.

    A record is either complete or an explicit stub — never both, never
    neither. Which fields carry the meaning is the registry's own business, so
    each subclass names them in `MEANING_FIELDS`: on a Special that is its
    `effect`, on a modifier its two numbers.
    """

    MEANING_FIELDS: ClassVar[tuple[str, ...]] = ("effect",)

    name: str
    effect: str | None = None
    signature: str | None = None
    variables: dict[str, VariableConfig] = Field(default_factory=dict)
    flavor: str | None = None
    """What the rule represents, rather than what it does."""

    example: str | None = None
    todo: str | None = None
    """What is missing. Its presence, never the absence of prose, marks a stub."""

    see_also: list[Ref] = Field(default_factory=list)
    """Editorial pointer: related reading, never load-bearing."""

    places: list[Ref] = Field(default_factory=list)
    """Mechanical consequence: this rule causes the referenced thing."""

    @model_validator(mode="after")
    def _check_completeness(self) -> Self:
        """Require a meaning field or `todo`, and allow both.

        A written rule may still carry an open question — whether two rules
        are duplicates, whether a fixed value wants a variable — and that
        question is only worth writing down if the countdown can see it.
        """
        written = any(getattr(self, field) for field in self.MEANING_FIELDS)
        if not written and self.todo is None:
            fields = " / ".join(self.MEANING_FIELDS)
            msg = f"{self.name!r}: a record needs {fields} or todo, and has neither"
            raise ValueError(msg)
        return self

    @property
    def written(self) -> bool:
        """Whether the rule itself is written, whatever `todo` also asks."""
        return any(getattr(self, field) for field in self.MEANING_FIELDS)


class SpecialRuleConfig(RuleRecord):
    slots: list[Slot] = Field(min_length=1)
    """Where this id may be used. Rendering derives its groups from this."""

    versions: dict[Ref, "VersionOverlay"] = Field(default_factory=dict)
    """Rule-local prose for a rule that reads differently per version, keyed by
    the very ref an instance's version argument carries — so the overlay is
    found by lookup and a key pointing nowhere is caught rather than ignored. A
    version with no overlay inherits the target's own text."""


class VersionOverlay(StrictModel):
    effect: str


class SpecialRulesConfig(StrictModel):
    special: dict[str, SpecialRuleConfig]


#
# Tokens
#
class TokenRuleConfig(RuleRecord):
    phases: list[t.PhaseName] = Field(default_factory=list)
    remove: str | None = None
    to_hit: Modifier | None = None
    to_be_hit: Modifier | None = None


class TokenRulesConfig(StrictModel):
    explanation: str
    tokens: dict[str, TokenRuleConfig]


#
# Hexes
#
class HexRuleConfig(RuleRecord):
    remove: str | None = None
    to_hit: Modifier | None = None
    to_be_hit: Modifier | None = None


class HexRulesConfig(StrictModel):
    explanation: str
    hexes: dict[str, HexRuleConfig]


#
# Terrain
#
class TerrainRuleConfig(RuleRecord):
    to_hit: Modifier | None = None
    to_be_hit: Modifier | None = None


class TerrainRulesConfig(StrictModel):
    explanation: str | None = None
    terrain: dict[str, TerrainRuleConfig]


#
# To-hit modifiers
#
class ModifierRuleConfig(RuleRecord):
    """A record whose meaning *is* its two numbers.

    `[distance.long] to_hit = "-2"` is not an unwritten rule, so keying
    completeness on `effect` here would manufacture stubs the countdown then
    has to look past.
    """

    MEANING_FIELDS: ClassVar[tuple[str, ...]] = ("to_hit", "to_be_hit")

    to_hit: Modifier | None = None
    to_be_hit: Modifier | None = None


class ModifiersConfig(StrictModel):
    """The five registries whose records are nothing but to-hit modifiers.

    Field order is the order the to-hit table renders them in.
    """

    speed: dict[str, ModifierRuleConfig]
    distance: dict[str, ModifierRuleConfig]
    angle: dict[str, ModifierRuleConfig]
    size: dict[str, ModifierRuleConfig]
    ability: dict[str, ModifierRuleConfig]


#
# Namespaces
#
class NamespaceConfig(StrictModel):
    """Where one namespace's registry lives, and what to call it.

    A namespace is an abstract name, not a path: decoupling the two is what
    keeps a ref two segments long and a table rename out of the Race files.
    """

    name: str
    file: str
    table: str
    group: str | None = None
    """Another namespace to render under, when the two share a display group."""


class DamageTypeRuleConfig(RuleRecord):
    """A category of harm — what a Resistance or an Immunity is against."""


class NamespacesConfig(StrictModel):
    namespaces: dict[str, NamespaceConfig]
    damage_type: dict[str, DamageTypeRuleConfig]
