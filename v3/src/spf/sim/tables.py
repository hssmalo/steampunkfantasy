"""Damage tables compiled for the simulator: rows looked up by a rolled value."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from spf.prose import plain
from spf.schemas.type_aliases import (
    AtLeastRoll,
    DamageRoll,
    DamageTable,
    DamageTableName,
    ExactRoll,
)
from spf.sim.effects import (
    Effect,
    RowReference,
    Unparsed,
    Vocabulary,
    parse_effect,
)

_NO_BLEED_FROM_BLEED = re.compile(
    r"bleed does not cause (?:more )?bleed", re.IGNORECASE
)
_HALF_FUTURE = re.compile(r"\bhalf\b.*\bfuture\b", re.IGNORECASE)
_ON_A_KILL = re.compile(r"\b(?:killed|dies|destroyed)\b", re.IGNORECASE)
_KILLED_BY_TOKEN = re.compile(r"killed by (?:bleed|poison)", re.IGNORECASE)
_AMPLIFY_DEFINED = re.compile(r"^amplify bleeding:", re.IGNORECASE)
_IMMUNE = re.compile(r"^immune to (?P<name>.+?)\.?$", re.IGNORECASE)


@dataclass(frozen=True, kw_only=True)
class NoteRules:
    """What a Damage table's notes change about how damage plays out."""

    bleed_causes_bleed: bool = True
    halve_future_on_kill: bool = False
    immune: frozenset[str] = frozenset()
    """Tokens the Unit never takes, by id."""
    unparsed: list[str] = field(default_factory=list)


def parse_notes(notes: list[str], *, vocabulary: Vocabulary) -> NoteRules:
    """Read the notes the simulator understands; report the rest as unparsed.

    Removing the Bleed or Poison that killed a Model, and what amplifying
    bleeding means, are already part of those Tokens, so such a note is
    recognized and changes nothing.
    """
    bleed_causes_bleed, halve, immune, unparsed = True, False, set[str](), []
    for note in notes:
        text = plain(note)
        recognized = bool(
            _KILLED_BY_TOKEN.search(text) or _AMPLIFY_DEFINED.search(text)
        )
        if _NO_BLEED_FROM_BLEED.search(text):
            bleed_causes_bleed, recognized = False, True
        if _HALF_FUTURE.search(text) and _ON_A_KILL.search(text):
            halve, recognized = True, True
        if (match := _IMMUNE.match(text)) and (
            token := vocabulary.tokens.get(match["name"].lower())
        ):
            immune.add(token)
            recognized = True
        if not recognized:
            unparsed.append(note)
    return NoteRules(
        bleed_causes_bleed=bleed_causes_bleed,
        halve_future_on_kill=halve,
        immune=frozenset(immune),
        unparsed=unparsed,
    )


def roll_label(roll: DamageRoll) -> str:
    """Spell a Damage roll the way the Damage row prints it."""
    match roll:
        case ExactRoll(value=value):
            return str(value)
        case AtLeastRoll(value=value):
            return f"{value}+"
        case _:
            return f"{roll.low}-{roll.high}"


def _bounds(roll: DamageRoll) -> tuple[int, int | None]:
    """Give the lowest and highest value a Damage roll matches; `None` is unbounded."""
    match roll:
        case ExactRoll(value=value):
            return value, value
        case AtLeastRoll(value=value):
            return value, None
        case _:
            return roll.low, roll.high


@dataclass(frozen=True, kw_only=True)
class CompiledRow:
    """One Damage row, keyed by its printed Damage roll."""

    label: str
    low: int
    high: int | None
    effects: list[Effect]


@dataclass(frozen=True, kw_only=True)
class CompiledTable:
    """A Damage table the simulator can roll on."""

    name: DamageTableName
    rows: list[CompiledRow]
    notes: NoteRules = field(default_factory=NoteRules)

    def row_for(self, value: int) -> CompiledRow | None:
        """Find the row a rolled value lands on.

        The top row reads as "N and higher"; a value below the lowest row, or in
        a gap between rows, has no effect.
        """
        for row in self.rows:
            if row.low <= value and (row.high is None or value <= row.high):
                return row
        top = max(self.rows, key=lambda row: row.low, default=None)
        if top is not None and value > (top.high or top.low):
            return top
        return None


def _inline_references(
    effects: list[Effect], earlier: Mapping[str, list[Effect]]
) -> list[Effect]:
    """Replace a Row reference with the effects of the earlier row it names."""
    inlined: list[Effect] = []
    for effect in effects:
        if not isinstance(effect, RowReference):
            inlined.append(effect)
        elif effect.label in earlier:
            inlined.extend(earlier[effect.label])
        else:
            inlined.append(Unparsed(text=f"As {effect.label}"))
    return inlined


def compile_table(
    name: DamageTableName, table: DamageTable, *, vocabulary: Vocabulary
) -> CompiledTable:
    """Compile a Damage table's rows for lookup, with Row references inlined."""
    earlier: dict[str, list[Effect]] = {}
    rows: list[CompiledRow] = []
    for row in table.rows:
        label = roll_label(row.roll)
        low, high = _bounds(row.roll)
        effects = _inline_references(
            parse_effect(row.effect, vocabulary=vocabulary), earlier
        )
        earlier[label] = effects
        rows.append(CompiledRow(label=label, low=low, high=high, effects=effects))
    return CompiledTable(
        name=name, rows=rows, notes=parse_notes(table.notes, vocabulary=vocabulary)
    )
