"""Special commands for the SteamPunkFantasy CLI."""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Annotated

import cyclopts
import pydantic
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from spf import races
from spf.console import stdout
from spf.frontends.cli.suggest import resolve_or_raise
from spf.registry import Registry, load_registry
from spf.render.rulebook import constraint_text
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
    app.command(list_specials, name="list")
    app.command(show_special, name="show")


@dataclass(frozen=True)
class SpecialRow:
    """One Special as the list prints it: marks, label, and one line of text."""

    marks: str
    """The UMAR column."""

    label: str
    """Identifier and Signature, uninterpolated."""

    text: str
    """The effect, or the first line of `todo`."""

    is_stub: bool
    """Whether the record is a Stub, so `text` is designer prose."""


def _build_row(key: str, rule: SpecialRuleConfig) -> SpecialRow:
    """Build the row for one Special record.

    A record is either written or an explicit Stub, so those are the only two
    registers a row has: rule text, or the designer prose standing in for it.
    """
    if rule.written:
        # An effect may run to several lines; the row is one logical line, so
        # it is folded rather than cut and the list stays greppable.
        text, is_stub = " ".join((rule.effect or "").split()), False
    else:
        # A Stub always has a `todo` — the schema admits no third state — and
        # only its first line fits a one-line row.
        text, is_stub = (rule.todo or "").splitlines()[0], True
    return SpecialRow(
        marks=_slot_marks(rule.slots),
        label=f"{key}{rule.signature or ''}",
        text=text,
        is_stub=is_stub,
    )


def special_rows(registry: Registry, *, slot: Slot | None = None) -> list[SpecialRow]:
    """Build one row per Special in the Registry, sorted by Identifier.

    `slot` keeps the Specials declaring it, whatever else they also declare.
    """
    return [
        _build_row(key, rule)
        for key, rule in sorted(registry.specials.items())
        if slot is None or slot in rule.slots
    ]


def list_specials(*, slot: Slot | None = None) -> None:
    """List every Special in the Registry, one row each.

    Uses UMAR prefixes for U=Unit, M=Model, A=Assault, R=Range specials, so a
    Special declaring several Slots is marked in each of their positions.
    """
    rows = special_rows(load_registry(), slot=slot)
    if not rows:
        return

    width = max(len(row.label) for row in rows)
    for row in rows:
        # Escaped before any markup is added, never after: a Signature is full
        # of square brackets, which Rich would otherwise swallow as tags.
        text = escape(row.text)
        # A `todo` is designer prose rather than rule text, so it reads as a
        # different register.
        text = f"[dim]todo: {text}[/]" if row.is_stub else text
        # Soft-wrapped rather than truncated: piped output is then one
        # greppable line per Special, with nothing lost.
        stdout.print(
            # Padded before escaping: an escape adds backslashes that Rich
            # then eats, so padding the escaped label would misalign the row.
            f"{row.marks} {escape(f'{row.label:<{width}}')} {text}",
            highlight=False,
            soft_wrap=True,
        )


@dataclass(frozen=True)
class SpecialRecord:
    """One Special as `show` prints it, above its Instances.

    Terminal-shaped rather than Rulebook-shaped: the Rulebook's `RuleEntry`
    assumes Markdown and is only built for written rules, while most records
    here are Stubs and every field is printed as plain text.
    """

    marks: str
    """The UMAR column."""

    label: str
    """Identifier and Signature, uninterpolated."""

    name: str
    """The Display Name."""

    effect: str | None
    flavor: str | None
    example: str | None

    variables: list[tuple[str, str]]
    """(name, constraint phrase) pairs, in declaration order."""

    places: list[str]
    """Rendered Refs: what this rule causes."""

    see_also: list[str]
    """Rendered Refs: related reading."""

    versions: list[tuple[str, str]]
    """(rendered Ref, effect) pairs, one per version overlay."""

    todo: str | None
    """The whole note, newlines intact — `show` has room for all of it."""


def _ref_label(ref: str, registry: Registry) -> str:
    """Render a Ref as the name a reader knows plus the id they can type."""
    return f"{registry.display_name(ref)} ({ref})"


def special_record(
    key: str, rule: SpecialRuleConfig, *, registry: Registry
) -> SpecialRecord:
    """Build the record block for one Special.

    Pure, as `special_rows` is: the Registry comes from the caller, so the
    Refs resolve (ADR 0024) without the builder reaching for a loader.
    """
    return SpecialRecord(
        marks=_slot_marks(rule.slots),
        label=f"{key}{rule.signature or ''}",
        name=rule.name,
        effect=rule.effect,
        flavor=rule.flavor,
        example=rule.example,
        variables=[
            (name, constraint_text(spec)) for name, spec in rule.variables.items()
        ],
        places=[_ref_label(ref, registry) for ref in rule.places],
        see_also=[_ref_label(ref, registry) for ref in rule.see_also],
        versions=[
            (_ref_label(ref, registry), overlay.effect)
            for ref, overlay in rule.versions.items()
        ],
        todo=rule.todo,
    )


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


_GUTTER = len("Variables")
"""The label column's width: the longest label the record block prints."""


def _print_record(record: SpecialRecord) -> None:
    """Print the rule itself: a header line, then a labeled block."""
    # Escaped before any markup is added, never after: a Signature is full of
    # square brackets, and a Display Name is author prose, either of which Rich
    # would otherwise read as tags.
    stdout.print(
        f"{record.marks} {escape(record.label)}  {escape(record.name)}",
        highlight=False,
    )
    stdout.print()

    # A grid rather than hand-laid columns: rule prose runs to several lines,
    # and only a table wraps it under the label gutter and keeps its newlines.
    grid = Table.grid(padding=(0, 2))
    # A fixed gutter rather than one sized to the record: every Special's block
    # then lines up, whichever fields it happens to carry.
    grid.add_column(no_wrap=True, width=_GUTTER)
    grid.add_column()
    fields: list[tuple[str, str | None]] = [
        ("Effect", record.effect),
        ("Flavor", record.flavor),
        ("Example", record.example),
    ]
    for label, value in fields:
        if value is not None:
            # `Text` rather than markup: rule prose is arbitrary author text,
            # and brackets in it are not tags.
            grid.add_row(label, Text(value.strip()))
    if record.variables:
        grid.add_row(
            "Variables",
            Text("\n".join(f"{name}: {phrase}" for name, phrase in record.variables)),
        )
    for label, refs in [("Places", record.places), ("See also", record.see_also)]:
        if refs:
            grid.add_row(label, Text("\n".join(refs)))
    if record.versions:
        grid.add_row("Versions", _versions_grid(record.versions))
    if record.todo is not None:
        # Designer prose rather than rule text, so it reads as a different
        # register — as it does in `spf special list`.
        grid.add_row("Todo", Text(record.todo.strip(), style="dim"))
    stdout.print(grid)


def _versions_grid(versions: list[tuple[str, str]]) -> Table:
    """Lay out the version overlays as a two-level sub-block.

    An overlay is a full alternative effect rather than a fragment, so each ref
    gets a line of its own with its text indented beneath.
    """
    grid = Table.grid()
    grid.add_column()
    for ref, effect in versions:
        grid.add_row(Text(ref))
        # Padded rather than prefixed, so the indent survives a wrap.
        grid.add_row(Padding(Text(effect.strip()), (0, 0, 0, 2)))
    return grid


def show_special(special_key: SpecialKey) -> None:
    """Show one Special's rule, then every Instance of it across the Races.

    Uses UMAR prefixes for U=Unit, M=Model, A=Assault, R=Range specials. Which
    of the four a rule is looked for in comes from the `slots` it declares, so
    the command asks the rule rather than keeping a vocabulary of its own.
    """
    registry = load_registry()
    rule = registry.specials[special_key]
    _print_record(special_record(special_key, rule, registry=registry))

    stdout.print()
    stdout.print("Instances")
    found = skipped = False
    for race_name in races.list_races():
        try:
            race = races.get_race(race_name)
        except pydantic.ValidationError:
            # Tolerant listing (ADR 0004) continues, but a silent skip is
            # indistinguishable from a Race holding no Instance.
            stdout.print(
                f"[dim]{race_name}: skipped (does not validate)[/]", highlight=False
            )
            skipped = True
            continue

        matches = _matches(race, key=special_key, rule=rule, registry=registry)
        if not matches:
            continue
        found = True

        display_name = escape(race.races[race_name].name)
        stdout.print(f"[bold]{display_name}[/] ({race_name})", highlight=False)
        for label, value in matches:
            # A signature is full of square brackets, which are Rich's own
            # markup: printed raw, `[range=1]` would vanish as a tag.
            stdout.print(f"  {label:<50} {escape(value)}", highlight=False)
    if not found:
        # "Unused" is only a claim about the Races that loaded: a skipped one
        # may well hold the Instances this says there are none of.
        where = " in the Races that validate" if skipped else ""
        stdout.print(f"[dim](none{where})[/]", highlight=False)
