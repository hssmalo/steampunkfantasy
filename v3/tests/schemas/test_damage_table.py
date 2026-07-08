"""Tests for the structured damage-table schema (issue #41)."""

import pytest
from pydantic import ValidationError

from spf.schemas.type_aliases import (
    AtLeastRoll,
    DamageTable,
    ExactRoll,
    RangeRoll,
)


def test_damage_table_parses_roll_variants_and_notes() -> None:
    table = DamageTable.model_validate(
        {
            "rows": ["1-2: Bleed[4]", "6+: shaken", "9: Unit destroyed"],
            "notes": ["Bleed does not cause more bleeding"],
        }
    )

    assert table.rows[0].roll == RangeRoll(low=1, high=2)
    assert table.rows[0].effect == "Bleed[4]"
    assert table.rows[1].roll == AtLeastRoll(value=6)
    assert table.rows[1].effect == "shaken"
    assert table.rows[2].roll == ExactRoll(value=9)
    assert table.rows[2].effect == "Unit destroyed"
    assert table.notes == ["Bleed does not cause more bleeding"]


def test_damage_table_notes_default_to_empty() -> None:
    table = DamageTable.model_validate({"rows": ["1: Fine"]})

    assert table.notes == []


def test_damage_table_row_without_separator_is_rejected() -> None:
    with pytest.raises(ValidationError, match="missing ':' separator"):
        DamageTable.model_validate({"rows": ["as regular damage"]})
