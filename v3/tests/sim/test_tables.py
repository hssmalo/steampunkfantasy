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
from spf.sim.tables import CompiledRow, NoteRules, Segment, compile_table

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


def _notes(*notes: str) -> NoteRules:
    table = DamageTable.model_validate({"rows": ["1: Dazed"], "notes": list(notes)})
    vocabulary = Vocabulary(tokens={"poison": "poison", "dazed": "dazed"})
    return compile_table("Regular", table, vocabulary=vocabulary).notes


def test_a_table_without_notes_changes_nothing() -> None:
    assert _notes() == NoteRules()


@pytest.mark.parametrize(
    "note",
    [
        "Bleed does not cause more Bleed",
        "Bleed does not cause more {Bleed[4]:token.bleed}",
        (
            "Bleed does not cause more {Bleed:token.bleed}. If a Bleed[N] would"
            " cause a Bleed[M] and M is higher than N, it is raised to Bleed[M]"
            " instead."
        ),
    ],
)
def test_a_bleed_note_is_recognized_and_changes_nothing(note: str) -> None:
    assert _notes(note) == NoteRules()


@pytest.mark.parametrize(
    "note",
    [
        "When one model is killed, half all +1 to future damage rounded down",
        "If one model is killed remove half of the +1 future damage tokens",
        "Remove half of the +1 future damage tokens when one robots dies",
    ],
)
def test_halving_future_damage_on_a_kill(note: str) -> None:
    assert _notes(note).halve_future_on_kill


def test_removing_the_token_that_killed_is_recognized() -> None:
    notes = _notes("If killed by Poison or Bleed, remove that instance")
    assert notes == NoteRules()


@pytest.mark.parametrize(
    "note",
    [
        (
            "When all models are temporarily killed: replace kill 1 model with +1"
            " to future damage and keep all remaining Bleed."
        ),
        (
            "When all models are temporarily killed: replace kill one model with"
            " +1 to future damage"
        ),
    ],
)
def test_replacing_a_kill_once_every_model_is_temporarily_killed(note: str) -> None:
    assert _notes(note) == NoteRules(
        replace_kill_when_all_temporarily_killed=(FutureDamage(amount=1),)
    )


def test_immunity_to_a_token() -> None:
    assert _notes("Immune to Poison").immune == frozenset({"poison"})


def test_an_unrecognized_note_is_unparsed() -> None:
    note = "Count the number of alive models before the apply damage step"
    assert _notes(note).unparsed == [note]


def test_a_reference_to_no_row_is_unparsed() -> None:
    assert _effects(["1: As 7, Kill 1 model"], 1) == [
        Unparsed(text="As 7"),
        Kill(count=1),
    ]


def _row(text: str, *, tokens: dict[str, str] | None = None) -> CompiledRow:
    table = compile_table(
        "Regular", _table(f"1: {text}"), vocabulary=Vocabulary(tokens=tokens or {})
    )
    return table.rows[0]


def test_a_fully_parsed_row_is_one_simulated_segment() -> None:
    assert _row("Kill 1 model").segments() == [
        Segment(text="Kill 1 model", simulated=True)
    ]


def test_an_unparsed_clause_is_marked_where_it_is_written() -> None:
    assert _row("Kill 1 model, Wobble twice, +2 to future damage").segments() == [
        Segment(text="Kill 1 model, ", simulated=True),
        Segment(text="Wobble twice", simulated=False),
        Segment(text=", +2 to future damage", simulated=True),
    ]


def test_a_segment_prints_a_rule_link_as_its_label() -> None:
    row = _row("{Wobble:token.wobble} twice, Kill 1 model")
    assert row.segments() == [
        Segment(text="Wobble twice", simulated=False),
        Segment(text=", Kill 1 model", simulated=True),
    ]


def test_an_unparsed_reference_to_no_row_is_marked() -> None:
    assert _row("As 7, Kill 1 model").segments() == [
        Segment(text="As 7", simulated=False),
        Segment(text=", Kill 1 model", simulated=True),
    ]


def test_a_table_keeps_its_notes_as_written() -> None:
    notes = ["Bleed does not cause more Bleed", "Count the models first"]
    table = compile_table(
        "Regular", _table("1: Dazed", notes=notes), vocabulary=VOCABULARY
    )
    assert table.written_notes == notes
