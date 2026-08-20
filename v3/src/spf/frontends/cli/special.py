"""Special commands for the SteamPunkFantasy CLI."""

from collections.abc import Sequence
from typing import Annotated, TypeIs, get_args

import cyclopts
import pydantic

from spf import races
from spf.console import stdout
from spf.frontends.cli.suggest import resolve_or_raise
from spf.schemas import type_aliases as t
from spf.schemas.race import RaceConfig

_UNIT_SPECIALS: frozenset[str] = frozenset(get_args(t.UnitSpecial.__value__))
_MODEL_SPECIALS: frozenset[str] = frozenset(get_args(t.ModelSpecial.__value__))
_ASSAULT_SPECIALS: frozenset[str] = frozenset(get_args(t.AssaultSpecial.__value__))
_RANGE_SPECIALS: frozenset[str] = frozenset(get_args(t.RangeSpecial.__value__))


def is_unit_special(key: str) -> TypeIs[t.UnitSpecial]:
    """Return True if key is a valid UnitSpecial."""
    return key in _UNIT_SPECIALS


def is_model_special(key: str) -> TypeIs[t.ModelSpecial]:
    """Return True if key is a valid ModelSpecial."""
    return key in _MODEL_SPECIALS


def is_assault_special(key: str) -> TypeIs[t.AssaultSpecial]:
    """Return True if key is a valid AssaultSpecial."""
    return key in _ASSAULT_SPECIALS


def is_range_special(key: str) -> TypeIs[t.RangeSpecial]:
    """Return True if key is a valid RangeSpecial."""
    return key in _RANGE_SPECIALS


def add_commands(app: cyclopts.App) -> None:
    """Add special commands to the CLI."""
    app.command(show_special, name="show")


# A special key is any of the four scopes' keys, spelled as a plain `str` so a
# mistyped one gets a "Did you mean ...?" instead of all four Literal unions
# dumped verbatim. The `TypeIs` guards below narrow it back per scope.
_SPECIALS = sorted(
    _UNIT_SPECIALS | _MODEL_SPECIALS | _ASSAULT_SPECIALS | _RANGE_SPECIALS
)


def _resolve_special_key(_type: type, tokens: Sequence[cyclopts.Token]) -> str:
    """Canonicalise a special key, or reject it with suggestions.

    A converter rather than a validator: a validator can only reject, and a key
    given in the wrong case is accepted and rewritten to its canonical spelling.
    """
    return resolve_or_raise(
        tokens[0].value, _SPECIALS, noun="special", see="spf rules specials"
    )


type SpecialKey = Annotated[str, cyclopts.Parameter(converter=_resolve_special_key)]


def _unit_matches(race: RaceConfig, *, key: t.UnitSpecial) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    matches.extend(
        (f"U    Unit:      {u.name}", u.special[key])
        for u in race.units.values()
        if key in u.special
    )
    matches.extend(
        (f"U    Model:     {m.name}", m.unit_special[key])
        for m in race.models.values()
        if key in m.unit_special
    )
    matches.extend(
        (f"U    Equipment: {e.name}", e.unit_special[key])
        for e in race.equipment.values()
        if key in e.unit_special
    )
    return matches


def _model_matches(race: RaceConfig, *, key: t.ModelSpecial) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    matches.extend(
        (f" M   Model:     {m.name}", m.special[key])
        for m in race.models.values()
        if key in m.special
    )
    matches.extend(
        (f" M   Equipment: {e.name}", e.model_special[key])
        for e in race.equipment.values()
        if key in e.model_special
    )
    return matches


def _assault_matches(
    race: RaceConfig, *, key: t.AssaultSpecial
) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    matches.extend(
        (f"  A  Model:     {m.name}", m.assault.special[key])
        for m in race.models.values()
        if key in m.assault.special
    )
    matches.extend(
        (f"  A  Equipment: {e.name}", e.assault.special[key])
        for e in race.equipment.values()
        if e.assault and key in e.assault.special
    )
    return matches


def _range_matches(race: RaceConfig, *, key: t.RangeSpecial) -> list[tuple[str, str]]:
    # Equipment only: a range profile hangs off equipment, never off a model.
    return [
        (f"   R Equipment: {e.name}", e.range.special[key])
        for e in race.equipment.values()
        if e.range is not None and key in e.range.special
    ]


def _collect_matches(
    race: RaceConfig, *, special_key: SpecialKey
) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    if is_unit_special(special_key):
        matches.extend(_unit_matches(race, key=special_key))
    if is_model_special(special_key):
        matches.extend(_model_matches(race, key=special_key))
    if is_assault_special(special_key):
        matches.extend(_assault_matches(race, key=special_key))
    if is_range_special(special_key):
        matches.extend(_range_matches(race, key=special_key))
    return matches


def show_special(special_key: SpecialKey) -> None:
    """Show all units, models, and equipment with a given special rule.

    Uses UMAR prefixes for U=Unit, M=Model, A=Assault, R=Range specials.
    """
    for race_name in races.list_races():
        stdout.print(race_name)

        try:
            race = races.get_race(race_name)
        except pydantic.ValidationError:
            continue

        matches = _collect_matches(race, special_key=special_key)
        if not matches:
            continue

        display_name = race.races[race_name].name
        stdout.print(f"[bold]{display_name}[/]")
        for label, value in matches:
            stdout.print(f"  {label:<50} {value}", highlight=False)
