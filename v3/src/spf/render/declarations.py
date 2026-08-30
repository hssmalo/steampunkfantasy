"""Rendering the constraints and deltas a catalogue declares but cannot resolve.

A Race's records are not fielded, so three kinds of value have no result yet,
only a declaration: the Holder capacity a Model offers, the requirements an
Equipment places on whoever carries it, and the `Stacker` deltas a Model or an
Equipment applies to stats it does not own. A Model's `+3/+2/0/0` armor grant
has no value until a specific Unit is fielded under it, so a catalogue prints
the delta itself and resolves nothing.

The Holder arithmetic these read is `spf.armies.holders`' business (ADR 0020);
here they are only shaped into prose.
"""

from collections.abc import Sequence

from spf.schemas import type_aliases as t
from spf.schemas.race import EquipmentAssaultConfig, Stacker, UnitStatModifierConfig

UNLIMITED = 999
"""The limit standing for an uncapped Holder, written `∞` in the data."""

INFINITY = "∞"

_ALTERNATIVE_SEPARATOR = " or "
"""Between the members of one requirement group, any one of which satisfies it."""

_TYPE_PREFIX = "Model type"

_ASSAULT_LABELS: tuple[tuple[str, str], ...] = (
    ("strength", "Strength"),
    ("strength_die", "Strength die"),
    ("deflection", "Deflection"),
    ("deflection_die", "Deflection die"),
    ("damage", "Damage"),
    ("ap", "AP"),
)
"""Each `EquipmentAssaultConfig` stacker field and the label it prints under."""

UNIT_TARGET = "its Unit"
"""What a `UnitStatModifierConfig` grant lands on, from the record's view."""


def limit_rows(limits: Sequence[t.EquipmentLimit]) -> list[tuple[str, str]]:
    """Pair each Holder with its capacity, in declaration order."""
    return [
        (limit.holder, INFINITY if limit.limit >= UNLIMITED else str(limit.limit))
        for limit in limits
    ]


def requirement_lines(requires: Sequence[Sequence[t.Requirement]]) -> list[str]:
    """Render `requires` as one line per group, each group's members a choice.

    `requires` is a conjunction of disjunctions: every group has to be
    satisfied, and any one member satisfies its group (see
    `spf.armies.build`). So the lines are what must *all* hold, and a caller
    joining them must not join them with an "or".

    A group of nothing but Model types shares one prefix — `Model type
    Infantry or Cavalry` — since repeating it per alternative reads as a
    longer list of different things than it is.
    """
    return [_group_text(group) for group in requires]


def _group_text(group: Sequence[t.Requirement]) -> str:
    """Render one requirement group: its members, any one of which will do."""
    if group and all(req.key == "type" for req in group):
        types = _ALTERNATIVE_SEPARATOR.join(str(req.value) for req in group)
        return f"{_TYPE_PREFIX} {types}"
    return _ALTERNATIVE_SEPARATOR.join(_requirement_text(req) for req in group)


def _requirement_text(requirement: t.Requirement) -> str:
    """Render one requirement: a Model type, or the Holder capacity it claims."""
    if requirement.key == "type":
        return f"{_TYPE_PREFIX} {requirement.value}"
    return f"{requirement.value} {requirement.key}"


def modifier_line[T](label: str, stacker: Stacker[T], *, target: str = "") -> str:
    """Render one declared delta: what it does to `label`, and to whose stat.

    An empty Stacker declares nothing and renders as nothing. Resolving one is
    an error, but a catalogue reports what it was given rather than judging it.
    """
    change = _change_text(stacker)
    if not change:
        return ""
    landing = f" to {target}" if target else ""
    return f"{label}: {change}{landing}"


def _change_text[T](stacker: Stacker[T]) -> str:
    """Render the change a Stacker declares, in the verb its variant implies."""
    if stacker.replace is not None:
        return f"set to {_value_text(stacker.replace, signed=False)}"
    if stacker.add is not None:
        return _value_text(stacker.add, signed=True)
    if stacker.extend is not None:
        return f"extended by {_value_text(stacker.extend, signed=False, join=', ')}"
    return ""


def _value_text(value: object, *, signed: bool, join: str = "/") -> str:
    """Render a Stacker's value, one cell per angle when it carries a list."""
    if isinstance(value, list):
        return join.join(_scalar_text(item, signed=signed) for item in value)
    return _scalar_text(value, signed=signed)


def _scalar_text(value: object, *, signed: bool) -> str:
    """Render one value, marking an added amount with the sign it carries."""
    if signed and isinstance(value, int) and value > 0:
        return f"+{value}"
    return str(value)


def unit_modifier_lines(unit: UnitStatModifierConfig | None) -> list[str]:
    """Render every stat a record declares a delta to on the Unit holding it."""
    if unit is None or unit.armor is None:
        return []
    line = modifier_line("Armor", unit.armor, target=UNIT_TARGET)
    return [line] if line else []


def assault_modifier_lines(assault: EquipmentAssaultConfig | None) -> list[str]:
    """Render every assault stat an Equipment declares a delta to."""
    if assault is None:
        return []
    lines = [
        modifier_line(label, stacker)
        for field, label in _ASSAULT_LABELS
        if (stacker := getattr(assault, field)) is not None
    ]
    return [line for line in lines if line]
