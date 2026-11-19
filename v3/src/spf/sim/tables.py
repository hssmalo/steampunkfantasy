"""Damage tables compiled for the simulator: rows looked up by a rolled value."""

from collections.abc import Mapping
from dataclasses import dataclass

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
    return CompiledTable(name=name, rows=rows)
