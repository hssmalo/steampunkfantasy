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
    Kill,
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
# Keeping the remaining Bleed needs no rule: a replaced kill is not a kill, so
# the Bleed that rolled is never removed for it.
_ALL_TEMPORARILY_KILLED = re.compile(
    r"^when all models are temporarily killed: replace kill (?:1|one) model with"
    r" (?P<effects>.+?)(?: and keep all remaining bleed)?\.?$",
    re.IGNORECASE,
)
_IMMUNE = re.compile(r"^immune to (?P<name>.+?)\.?$", re.IGNORECASE)


@dataclass(frozen=True, kw_only=True)
class NoteRules:
    """What a Damage table's notes change about how damage plays out."""

    halve_future_on_kill: bool = False
    immune: frozenset[str] = frozenset()
    """Tokens the Unit never takes, by id."""
    replace_kill_when_all_temporarily_killed: tuple[Effect, ...] = ()
    """What a kill does instead once every Model is temporarily killed."""
    unparsed: list[str] = field(default_factory=list)


def _replacement(text: str, vocabulary: Vocabulary) -> tuple[Effect, ...] | None:
    """Read what replaces a kill once every Model is temporarily killed.

    A replacement that is not fully parsed, or that kills again, is not followed.
    """
    if not (match := _ALL_TEMPORARILY_KILLED.match(text)):
        return None
    effects = tuple(parse_effect(match["effects"], vocabulary=vocabulary))
    if any(isinstance(effect, Kill | RowReference | Unparsed) for effect in effects):
        return None
    return effects


def parse_notes(notes: list[str], *, vocabulary: Vocabulary) -> NoteRules:
    """Read the notes the simulator understands; report the rest as unparsed.

    Removing the Bleed or Poison that killed a Model, what amplifying
    bleeding means, and that a Bleed never causes a new Bleed are already part
    of those Tokens, so such a note is recognized and changes nothing.
    """
    halve, immune, unparsed = False, set[str](), []
    replacement: tuple[Effect, ...] = ()
    for note in notes:
        text = plain(note)
        recognized = bool(
            _KILLED_BY_TOKEN.search(text)
            or _AMPLIFY_DEFINED.search(text)
            or _NO_BLEED_FROM_BLEED.search(text)
        )
        if _HALF_FUTURE.search(text) and _ON_A_KILL.search(text):
            halve, recognized = True, True
        if (match := _IMMUNE.match(text)) and (
            token := vocabulary.tokens.get(match["name"].lower())
        ):
            immune.add(token)
            recognized = True
        if (effects := _replacement(text, vocabulary)) is not None:
            replacement += effects
            recognized = True
        if not recognized:
            unparsed.append(note)
    return NoteRules(
        halve_future_on_kill=halve,
        immune=frozenset(immune),
        replace_kill_when_all_temporarily_killed=replacement,
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
class Segment:
    """A stretch of a Damage row's text, and whether the simulator plays it."""

    text: str
    simulated: bool


@dataclass(frozen=True, kw_only=True)
class CompiledRow:
    """One Damage row, keyed by its printed Damage roll."""

    label: str
    low: int
    high: int | None
    effects: list[Effect]
    text: str = ""
    """The effect as written, Rule Links included."""

    def segments(self) -> list[Segment]:
        """Split the written effect into stretches the simulator plays or skips.

        An unparsed clause inlined from an earlier row is not written here, so
        it is marked on that row instead.
        """
        segments: list[Segment] = []
        cursor = 0
        for effect in self.effects:
            if not isinstance(effect, Unparsed):
                continue
            if (at := self.text.find(effect.text, cursor)) < 0:
                continue
            segments.append(Segment(text=self.text[cursor:at], simulated=True))
            cursor = at + len(effect.text)
            segments.append(Segment(text=self.text[at:cursor], simulated=False))
        segments.append(Segment(text=self.text[cursor:], simulated=True))
        return [
            Segment(text=plain(segment.text), simulated=segment.simulated)
            for segment in segments
            if segment.text
        ]


@dataclass(frozen=True, kw_only=True)
class CompiledTable:
    """A Damage table the simulator can roll on."""

    name: DamageTableName
    rows: list[CompiledRow]
    notes: NoteRules = field(default_factory=NoteRules)
    written_notes: list[str] = field(default_factory=list)
    """The notes as written, Rule Links included."""

    def row_for(self, value: int) -> CompiledRow | None:
        """Find the row a rolled value lands on.

        A value below the lowest row, or in a gap between rows, has no effect.
        """
        for row in self.rows:
            if row.low <= value and (row.high is None or value <= row.high):
                return row
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
        rows.append(
            CompiledRow(
                label=label, low=low, high=high, effects=effects, text=row.effect
            )
        )
    return CompiledTable(
        name=name,
        rows=rows,
        notes=parse_notes(table.notes, vocabulary=vocabulary),
        written_notes=list(table.notes),
    )
