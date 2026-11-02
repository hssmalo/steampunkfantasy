"""Rendering a damage table.

Pure over a parsed `DamageRoll`, which every Product printing a Unit's damage
tables needs in the same shape whether it reads a resolved Army or a
`RaceConfig`.
"""

from collections.abc import Mapping

from spf.prose import AnchorOf, LinkedText, linked_prose
from spf.schemas import type_aliases as t

type DamageTableEntry = tuple[str, list[tuple[str, LinkedText]], list[LinkedText]]
"""(table name, (roll, effect) rows, notes) as a template prints them."""


def roll_text(roll: t.DamageRoll) -> str:
    """Render a damage roll as its table-column string (`9` / `1-2` / `6+`)."""
    match roll:
        case t.ExactRoll(value=value):
            return str(value)
        case t.RangeRoll(low=low, high=high):
            return f"{low}-{high}"
        case t.AtLeastRoll(value=value):
            return f"{value}+"


def damage_table_entries(
    tables: Mapping[t.DamageTableName, t.DamageTable], *, anchor_of: AnchorOf | None
) -> list[DamageTableEntry]:
    """Shape a Unit's damage tables, resolving each Rule Link against `anchor_of`."""
    return [
        (
            name,
            [
                (roll_text(row.roll), linked_prose(row.effect, anchor_of))
                for row in table.rows
            ],
            [linked_prose(note, anchor_of) for note in table.notes],
        )
        for name, table in tables.items()
    ]
