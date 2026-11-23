"""`spf sim damage` against a live Unit: the report's shape, never its numbers.

The Unit is picked at run time from whatever the committed Races hold, so no
rules edit can break these tests.
"""

from typing import cast

import pytest
from rich.text import Text

from spf import races
from spf.console import stdout
from spf.frontends.cli import app
from spf.frontends.cli.sim import UNPARSED_STYLE, damage_table, token_columns
from spf.schemas.type_aliases import DamageTable, RaceName
from spf.sim.effects import Vocabulary
from spf.sim.report import RoundSummary
from spf.sim.tables import CompiledTable, compile_table


@pytest.fixture(autouse=True)
def _wide_console(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stdout, "width", 200)


def _live_unit() -> tuple[str, str]:
    """Any committed Unit with a Regular Damage table, as `race.unit`."""
    for race_name in races.list_races(validate=True):
        for key, unit in races.get_units(race_name).items():
            if "Regular" in unit.damage_tables:
                return f"{race_name}.{key}", unit.name
    pytest.skip("no committed Unit has a Regular Damage table")


def _sim(*args: str) -> None:
    app(["sim", "damage", *args], exit_on_error=False, result_action="return_value")


def test_damage_reports_a_live_unit(capsys: pytest.CaptureFixture[str]) -> None:
    unit, name = _live_unit()
    _sim(unit, "--start", "d6, bleed=4, future=1", "--runs", "50", "--seed", "7")
    out = capsys.readouterr().out
    assert name in out
    assert "seed 7" in out
    assert "50 runs" in out
    assert "P(Destroyed)" in out


def test_attrition_reports_a_live_unit(capsys: pytest.CaptureFixture[str]) -> None:
    unit, name = _live_unit()
    _sim(unit, "--incoming", "d6-2", "--runs", "20", "--max-rounds", "3")
    assert name in capsys.readouterr().out


def test_an_unknown_unit_is_rejected_with_a_suggestion() -> None:
    unit, _ = _live_unit()
    with pytest.raises(ValueError, match="Did you mean"):
        _sim(f"{unit}x", "--start", "d6")


def test_a_bad_start_names_the_option() -> None:
    unit, _ = _live_unit()
    with pytest.raises(ValueError, match="--start"):
        _sim(unit, "--start", "bleed")


def test_damage_prints_the_units_tables_above_the_report(
    capsys: pytest.CaptureFixture[str],
) -> None:
    unit, _ = _live_unit()
    _sim(unit, "--start", "d6", "--runs", "5")
    out = capsys.readouterr().out
    assert "Regular damage table" in out
    assert out.index("Regular damage table") < out.index("P(Destroyed)")


def _sim_race(*args: str) -> None:
    app(
        ["sim", "damage-race", *args], exit_on_error=False, result_action="return_value"
    )


def test_damage_race_reports_one_line_per_unit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    unit, _ = _live_unit()
    race_name = unit.partition(".")[0]
    names = [
        config.name
        for config in races.get_units(cast("RaceName", race_name)).values()
        if "Regular" in config.damage_tables
    ]
    _sim_race(race_name, "--start", "d6, bleed=4", "--runs", "3", "--seed", "7")
    out = capsys.readouterr().out
    assert "seed 7" in out
    assert "P(Destroyed)" in out
    for name in names:
        assert name in out


def test_damage_race_rejects_an_unknown_race() -> None:
    unit, _ = _live_unit()
    with pytest.raises(ValueError, match="Did you mean"):
        _sim_race(f"{unit.partition('.')[0]}x", "--start", "d6")


def _compiled(*rows: str, notes: list[str] | None = None) -> CompiledTable:
    table = DamageTable.model_validate({"rows": list(rows), "notes": notes or []})
    return compile_table("Regular", table, vocabulary=Vocabulary(tokens={}))


def _styles(text: Text) -> dict[str, str]:
    """Map each styled stretch of a cell to its style."""
    return {text.plain[span.start : span.end]: str(span.style) for span in text.spans}


def test_an_unparsed_stretch_is_colored() -> None:
    table = damage_table(_compiled("1: Kill 1 model, Wobble twice"))
    effect = cast("Text", next(iter(table.columns[1].cells)))
    assert effect.plain == "Kill 1 model, Wobble twice"
    assert _styles(effect) == {"Wobble twice": UNPARSED_STYLE}


def _round(**tokens: float) -> RoundSummary:
    return RoundSummary(round=0, models=1.0, future=0.0, future_crew=0.0, tokens=tokens)


def test_token_columns_order_strengths_by_size() -> None:
    per_round = [
        _round(**{"bleed[10]": 0.1, "shaken": 1.0}),
        _round(**{"bleed[4]": 0.5, "poison[6]": 0.2, "bleed[6]": 0.3}),
    ]
    assert token_columns(per_round) == [
        "bleed[4]",
        "bleed[6]",
        "bleed[10]",
        "poison[6]",
        "shaken",
    ]


def test_an_unparsed_note_is_colored() -> None:
    notes = ["Bleed does not cause more Bleed", "Count the models first"]
    table = damage_table(_compiled("1: Kill 1 model", notes=notes))
    caption = cast("Text", table.caption)
    assert "Bleed does not cause more Bleed" in caption.plain
    assert _styles(caption) == {"Count the models first": UNPARSED_STYLE}
