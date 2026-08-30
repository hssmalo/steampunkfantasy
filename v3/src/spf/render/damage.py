"""Rendering the roll column of a damage table.

Pure over a parsed `DamageRoll`, which every Product printing a Unit's damage
tables needs in the same shape whether it reads a resolved Army or a
`RaceConfig`.
"""

from spf.schemas import type_aliases as t


def roll_text(roll: t.DamageRoll) -> str:
    """Render a damage roll as its table-column string (`9` / `1-2` / `6+`)."""
    match roll:
        case t.ExactRoll(value=value):
            return str(value)
        case t.RangeRoll(low=low, high=high):
            return f"{low}-{high}"
        case t.AtLeastRoll(value=value):
            return f"{value}+"
