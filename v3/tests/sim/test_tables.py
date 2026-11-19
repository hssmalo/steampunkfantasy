"""Looking up a Damage row for a rolled value, on synthetic Damage tables."""

import pytest

from spf.schemas.type_aliases import DamageTable
from spf.sim.effects import Vocabulary
from spf.sim.tables import compile_table

VOCABULARY = Vocabulary(tokens={})


def _table(*rows: str, notes: list[str] | None = None) -> DamageTable:
    return DamageTable.model_validate({"rows": list(rows), "notes": notes or []})


def _label(rows: list[str], value: int) -> str | None:
    table = compile_table("Regular", _table(*rows), vocabulary=VOCABULARY)
    row = table.row_for(value)
    return None if row is None else row.label


@pytest.mark.parametrize(
    ("value", "label"), [(2, "2-3"), (3, "2-3"), (4, "4"), (5, "5+"), (9, "5+")]
)
def test_each_roll_shape_matches(value: int, label: str) -> None:
    assert _label(["2-3: A", "4: B", "5+: C"], value) == label


def test_above_the_top_row_reads_as_the_top_row() -> None:
    assert _label(["1-3: A", "4-18: Unit Destroyed"], 19) == "4-18"
    assert _label(["1: A", "2: B"], 7) == "2"


def test_below_the_lowest_row_has_no_effect() -> None:
    assert _label(["4-5: A", "6: B"], 3) is None
    assert _label(["1: A"], -2) is None


def test_a_gap_between_rows_has_no_effect() -> None:
    assert _label(["1-2: A", "5: B"], 3) is None
