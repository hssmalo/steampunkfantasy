"""Looking up a Damage row for a rolled value, on synthetic Damage tables."""

import pytest

from spf.schemas.type_aliases import DamageTable
from spf.sim.effects import (
    Effect,
    FutureDamage,
    Kill,
    PlaceToken,
    Unparsed,
    Vocabulary,
)
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


def _effects(rows: list[str], value: int) -> list[Effect]:
    table = compile_table(
        "Regular", _table(*rows), vocabulary=Vocabulary(tokens={"dazed": "dazed"})
    )
    row = table.row_for(value)
    assert row is not None
    return row.effects


def test_a_row_carries_its_parsed_effects() -> None:
    assert _effects(["1: Kill 1 model"], 1) == [Kill(count=1)]


def test_a_row_reference_inlines_the_earlier_row() -> None:
    rows = ["1-3: Dazed", "4: As 1-3, Kill 1 model", "5: As 4, +2 to future damage"]
    assert _effects(rows, 4) == [PlaceToken(name="dazed"), Kill(count=1)]
    assert _effects(rows, 5) == [
        PlaceToken(name="dazed"),
        Kill(count=1),
        FutureDamage(amount=2),
    ]


def test_a_reference_to_no_row_is_unparsed() -> None:
    assert _effects(["1: As 7, Kill 1 model"], 1) == [
        Unparsed(text="As 7"),
        Kill(count=1),
    ]
