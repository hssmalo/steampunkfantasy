"""Tests for the rows `spf special list` prints.

`special_rows` is a pure function over the Registry, so most of these build
`SpecialRuleConfig` records by hand rather than coupling to `rules/special.toml`.
"""

import re

import pytest

from spf.frontends.cli import app
from spf.frontends.cli.special import special_rows
from spf.registry import Registry, load_registry
from spf.schemas.rules import SpecialRuleConfig

REGISTRY = load_registry()

_ROW = re.compile(r"^(?P<marks>[UMAR ]{4}) (?P<label>\S+)")
"""A printed row: the UMAR column, then the Identifier and its Signature."""


def _list(*args: str) -> None:
    app(["special", "list", *args], exit_on_error=False, result_action="return_value")


def _registry(**specials: SpecialRuleConfig) -> Registry:
    return Registry(records={"special": dict(specials)})


def _rule(**kwargs: object) -> SpecialRuleConfig:
    kwargs.setdefault("name", "Rule")
    kwargs.setdefault("slots", ["unit"])
    return SpecialRuleConfig.model_validate(kwargs)


def test_rows_come_back_sorted_by_identifier() -> None:
    registry = _registry(
        zeal=_rule(effect="Zealous."),
        aim=_rule(effect="Aimed."),
        march=_rule(effect="Marching."),
    )

    rows = special_rows(registry)

    assert [row.label for row in rows] == ["aim", "march", "zeal"]


def test_a_multi_slot_special_is_one_row_with_combined_marks() -> None:
    # The list is a view of the Registry, where a multi-Slot Special is one
    # record, so it stays one row with both positions marked.
    registry = _registry(to_hit=_rule(slots=["unit", "range"], effect="Hits."))

    (row,) = special_rows(registry)

    assert row.marks == "U  R"


def test_a_single_slot_specials_marks_match_the_show_column() -> None:
    registry = _registry(
        aim=_rule(slots=["unit"], effect="."),
        fend=_rule(slots=["model"], effect="."),
        hack=_rule(slots=["assault"], effect="."),
        snipe=_rule(slots=["range"], effect="."),
    )

    marks = {row.label: row.marks for row in special_rows(registry)}

    assert marks == {"aim": "U   ", "fend": " M  ", "hack": "  A ", "snipe": "   R"}


def test_the_signature_is_appended_uninterpolated() -> None:
    # Uninterpolated: the list is a view of the record, and the placeholder is
    # what tells a reader the Special takes an argument at all.
    registry = _registry(
        ork_reroll=_rule(
            signature="[{N}]",
            variables={"N": {"type": "int", "min": 1}},
            effect="Reroll.",
        )
    )

    (row,) = special_rows(registry)

    assert row.label == "ork_reroll[{N}]"


def test_a_written_rules_text_is_its_effect() -> None:
    registry = _registry(aim=_rule(effect="Aim carefully."))

    (row,) = special_rows(registry)

    assert row.text == "Aim carefully."
    assert row.is_stub is False


def test_a_slot_keeps_every_special_declaring_it() -> None:
    # A multi-Slot Special belongs to each Slot it declares, and keeps its
    # combined marks there — the filter chooses rows, it does not rewrite them.
    registry = _registry(
        to_hit=_rule(slots=["unit", "range"], effect="."),
        snipe=_rule(slots=["range"], effect="."),
        fend=_rule(slots=["model"], effect="."),
    )

    rows = special_rows(registry, slot="range")

    assert [(row.label, row.marks) for row in rows] == [
        ("snipe", "   R"),
        ("to_hit", "U  R"),
    ]


def test_no_slot_returns_every_record_once() -> None:
    registry = _registry(
        to_hit=_rule(slots=["unit", "range"], effect="."),
        fend=_rule(slots=["model"], effect="."),
    )

    rows = special_rows(registry)

    assert sorted(row.label for row in rows) == ["fend", "to_hit"]


def test_a_stubs_text_is_the_first_line_of_its_todo() -> None:
    # A `todo` can run to a paragraph, and the row is one line.
    registry = _registry(aim=_rule(todo="Rule text not yet written.\nAsk Hans."))

    (row,) = special_rows(registry)

    assert row.text == "Rule text not yet written."
    assert row.is_stub is True


def test_a_multi_line_effect_is_collapsed_onto_one_line() -> None:
    # An effect may be a list of options; the row is one logical line, so it is
    # folded rather than cut — a piped list stays one line per Special.
    registry = _registry(heal=_rule(effect="Spend points:\n\n- Cure. Cost 1.\n"))

    (row,) = special_rows(registry)

    assert row.text == "Spend points: - Cure. Cost 1."


def test_every_registered_special_is_exactly_one_printed_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _list()
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]

    assert len(lines) == len(REGISTRY.specials)


def test_every_registered_special_gets_a_row_with_text() -> None:
    rows = special_rows(REGISTRY)

    assert len(rows) == len(REGISTRY.specials)
    assert all(row.text for row in rows)


def test_the_printed_list_marks_a_stub_as_a_todo(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _list()

    assert "todo: " in capsys.readouterr().out


def test_the_printed_list_keeps_a_signatures_brackets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A Signature is full of square brackets, which are Rich's own markup:
    # printed raw, `[{N}]` would vanish as a tag.
    _list()

    assert "ork_reroll[{N}]" in capsys.readouterr().out


def test_the_printed_list_narrows_to_one_slot(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _list("--slot", "range")
    # A row is the UMAR column, then the label: read the label back off it
    # rather than counting columns.
    rows = (_ROW.match(line) for line in capsys.readouterr().out.splitlines())
    labels = {row["label"] for row in rows if row is not None}

    assert "sniper" in labels
    assert not any(label.startswith("assault_") for label in labels), (
        "an assault-only Special has no place under --slot range"
    )


def test_a_written_rule_carrying_a_todo_still_shows_its_effect() -> None:
    # A written rule may keep an open question; the rule text is what it has.
    registry = _registry(aim=_rule(effect="Aim carefully.", todo="Duplicate of fend?"))

    (row,) = special_rows(registry)

    assert row.text == "Aim carefully."
    assert row.is_stub is False
