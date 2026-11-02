"""Shaping a Unit's damage tables for the templates to print.

Pure over the parsed tables, which every Product printing them needs in the same
shape whether it reads a resolved Army or a `RaceConfig`.
"""

from collections.abc import Mapping
from typing import NamedTuple

from spf.prose import AnchorOf, LinkedText, linked_prose
from spf.schemas import type_aliases as t


class DamageTableView(NamedTuple):
    """One damage table as a template prints it."""

    name: str
    rows: list[tuple[str, LinkedText]]
    """(roll, effect) per row."""
    notes: list[LinkedText]


def roll_text(roll: t.DamageRoll) -> str:
    """Render a damage roll as its table-column string (`9` / `1-2` / `6+`)."""
    match roll:
        case t.ExactRoll(value=value):
            return str(value)
        case t.RangeRoll(low=low, high=high):
            return f"{low}-{high}"
        case t.AtLeastRoll(value=value):
            return f"{value}+"


def damage_table_views(
    tables: Mapping[t.DamageTableName, t.DamageTable], *, anchor_of: AnchorOf | None
) -> list[DamageTableView]:
    """Shape a Unit's damage tables, resolving each Rule Link against `anchor_of`."""
    return [
        DamageTableView(
            name=name,
            rows=[
                (roll_text(row.roll), linked_prose(row.effect, anchor_of))
                for row in table.rows
            ],
            notes=[linked_prose(note, anchor_of) for note in table.notes],
        )
        for name, table in tables.items()
    ]
