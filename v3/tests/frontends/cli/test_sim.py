"""`spf sim damage` against a live Unit: the report's shape, never its numbers.

The Unit is picked at run time from whatever the committed Races hold, so no
rules edit can break these tests.
"""

import pytest

from spf import races
from spf.console import stdout
from spf.frontends.cli import app


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
    assert "P(Unit Destroyed)" in out


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
