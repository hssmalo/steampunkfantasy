"""Special commands for the SteamPunkFantasy CLI."""

from collections.abc import Collection, Sequence
from typing import Annotated

import cyclopts
import pydantic
from rich.markup import escape

from spf import races
from spf.console import stdout
from spf.frontends.cli.suggest import resolve_or_raise
from spf.registry import Registry, load_registry
from spf.render.specials import special_row
from spf.schemas.race import RaceConfig
from spf.schemas.rules import Slot, SpecialRuleConfig
from spf.schemas.special import Specials

_SLOT_ORDER: tuple[Slot, ...] = ("unit", "model", "assault", "range")
"""The Slots the UMAR column has a position for, in the order it prints them."""


def _slot_marks(slots: Collection[Slot]) -> str:
    """Build the UMAR column: one fixed position per Slot, blank where absent.

    A Special may declare several Slots, so the column is built from a set
    rather than looked up: fixed positions are what let a reader scan the
    column, and what lets a multi-Slot record stay one row.
    """
    return "".join(slot[0].upper() if slot in slots else " " for slot in _SLOT_ORDER)


def add_commands(app: cyclopts.App) -> None:
    """Add special commands to the CLI."""
    app.command(show_special, name="show")


def _resolve_special_key(_type: type, tokens: Sequence[cyclopts.Token]) -> str:
    """Canonicalise a Special id, or reject it with suggestions.

    A converter rather than a validator: a validator can only reject, and an id
    given in the wrong case is accepted and rewritten to its canonical
    spelling. The corpus is the Special registry's key set, so a rule added to
    `rules/special.toml` is offered here without a second list to maintain.
    """
    return resolve_or_raise(
        tokens[0].value,
        sorted(load_registry().specials),
        noun="special",
        see="spf rules specials",
    )


type SpecialKey = Annotated[str, cyclopts.Parameter(converter=_resolve_special_key)]


def _holders(race: RaceConfig, slot: Slot) -> list[tuple[str, Specials]]:
    """Every (label, instances) pair one slot of a Race can hold.

    Which holders a slot reaches is the slot's own shape: a Unit Special may be
    granted by the Unit, by a Model or by Equipment, while a Range Special
    hangs off Equipment alone, because a range profile never sits on a Model.
    """
    mark = _slot_marks([slot])
    models = race.models.values()
    equipment = race.equipment.values()
    match slot:
        case "unit":
            return [
                *(
                    (f"{mark} Unit:      {u.name}", u.specials)
                    for u in race.units.values()
                ),
                *((f"{mark} Model:     {m.name}", m.unit_specials) for m in models),
                *((f"{mark} Equipment: {e.name}", e.unit_specials) for e in equipment),
            ]
        case "model":
            return [
                *((f"{mark} Model:     {m.name}", m.specials) for m in models),
                *((f"{mark} Equipment: {e.name}", e.model_specials) for e in equipment),
            ]
        case "assault":
            return [
                *((f"{mark} Model:     {m.name}", m.assault.specials) for m in models),
                *(
                    (f"{mark} Equipment: {e.name}", e.assault.specials)
                    for e in equipment
                    if e.assault is not None
                ),
            ]
        case "range":
            return [
                (f"{mark} Equipment: {e.name}", e.range.specials)
                for e in equipment
                if e.range is not None
            ]


def _matches(
    race: RaceConfig, *, key: str, rule: SpecialRuleConfig, registry: Registry
) -> list[tuple[str, str]]:
    """Every row one Race contributes for a Special id.

    A slot holds N instances of an id, so a holder contributes as many rows as
    it has occurrences rather than the single one a label dict could hold.
    """
    matches: list[tuple[str, str]] = []
    for slot in rule.slots:
        for label, specials in _holders(race, slot):
            for instance in specials.get(key, []):
                heading, text = special_row(key, instance, registry=registry)
                # The id is what was asked for, so repeating the rule's own
                # name says nothing; an atmospheric one is what the reader
                # could not have guessed, and leads the row.
                if heading == rule.name:
                    matches.append((label, text or heading))
                elif text:
                    matches.append((label, f"{heading}: {text}"))
                else:
                    matches.append((label, heading))
    return matches


def show_special(special_key: SpecialKey) -> None:
    """Show all units, models, and equipment with a given special rule.

    Uses UMAR prefixes for U=Unit, M=Model, A=Assault, R=Range specials. Which
    of the four a rule is looked for in comes from the `slots` it declares, so
    the command asks the rule rather than keeping a vocabulary of its own.
    """
    registry = load_registry()
    rule = registry.specials[special_key]
    for race_name in races.list_races():
        stdout.print(race_name)

        try:
            race = races.get_race(race_name)
        except pydantic.ValidationError:
            continue

        matches = _matches(race, key=special_key, rule=rule, registry=registry)
        if not matches:
            continue

        display_name = race.races[race_name].name
        stdout.print(f"[bold]{display_name}[/]")
        for label, value in matches:
            # A signature is full of square brackets, which are Rich's own
            # markup: printed raw, `[range=1]` would vanish as a tag.
            stdout.print(f"  {label:<50} {escape(value)}", highlight=False)
