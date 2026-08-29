"""Tests for the lists `spf race units|models|equipment|things` print.

These drive the real CLI against a tracked Race rather than a hand-built
`RaceConfig`: the subject is the printed row, and `races/goblin.toml` already
carries both a costed Unit and one with no Cost at all.
"""

import re

import cyclopts
import pytest
from rich.text import Text

from spf import races
from spf.console import stdout
from spf.frontends.cli import app
from spf.frontends.cli.race import _NO_COST

RACE = "goblin"
"""A tracked Race holding both costed and cost-less Units."""

_ROW = re.compile(r"^- (?P<name>\S.*?)\s\s+(?P<cost>\S.*?)\s*$")
"""A printed row: the name, then the cost column two or more spaces later."""

_COST_FIELDS = ("ip", "mp", "xp", "cp", "vpm")


@pytest.fixture(autouse=True)
def _unfolded_console(monkeypatch: pytest.MonkeyPatch) -> None:
    """Print wide enough that a row is never folded onto a second line.

    These tests read a name and a cost back off one line, so the width has to
    be the test's own rather than the terminal the suite is run from.
    """
    monkeypatch.setattr(stdout, "_width", 200)


def _race(*args: str) -> None:
    app(["race", *args], exit_on_error=False, result_action="return_value")


def _plain(markup: str) -> str:
    """Strip the Rich markup a cost string carries, as the console does."""
    return Text.from_markup(markup).plain


def _rows(out: str) -> list[tuple[str, str]]:
    """Read (name, cost) back off every row in a capture."""
    matches = (_ROW.match(line) for line in out.splitlines())
    return [(row["name"], row["cost"]) for row in matches if row is not None]


def _cost_of(rows: list[tuple[str, str]], name: str) -> str:
    return next(cost for row_name, cost in rows if row_name == name)


def test_units_prints_one_row_per_unit(capsys: pytest.CaptureFixture[str]) -> None:
    race = races.get_race(RACE)

    _race("units", RACE)
    rows = _rows(capsys.readouterr().out)

    assert sorted(name for name, _ in rows) == sorted(
        unit.name for unit in race.units.values()
    )


def test_models_prints_one_row_per_model(capsys: pytest.CaptureFixture[str]) -> None:
    race = races.get_race(RACE)

    _race("models", RACE)
    rows = _rows(capsys.readouterr().out)

    assert sorted(name for name, _ in rows) == sorted(
        model.name for model in race.models.values()
    )


def test_equipment_prints_one_row_per_equipment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    race = races.get_race(RACE)

    _race("equipment", RACE)
    rows = _rows(capsys.readouterr().out)

    # Sorted lists, not sets: two Equipment records may share a name, and both
    # of them still get a row.
    assert sorted(name for name, _ in rows) == sorted(
        equipment.name for equipment in race.equipment.values()
    )


def test_a_units_row_shows_every_number_of_its_cost(
    capsys: pytest.CaptureFixture[str],
) -> None:
    race = races.get_race(RACE)
    costed = {unit.name: unit.cost for unit in race.units.values() if unit.cost}
    assert costed, f"{RACE} is only useful here while it prices some of its Units"

    _race("units", RACE)
    rows = _rows(capsys.readouterr().out)

    for name, cost in costed.items():
        printed = _cost_of(rows, name)
        assert [
            field
            for field in _COST_FIELDS
            if f"{getattr(cost, field)}{field}" in printed
        ] == list(_COST_FIELDS), f"{name}: {printed}"


def test_a_units_row_shows_its_own_cost_not_the_next_ones(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Rows are sorted by cost, so a row printed against the wrong Unit still
    # survives the check above unless the costs differ.
    race = races.get_race(RACE)
    by_name = {
        unit.name: str(unit.cost) if unit.cost else _NO_COST
        for unit in race.units.values()
    }

    _race("units", RACE)
    rows = _rows(capsys.readouterr().out)

    assert dict(rows) == {name: _plain(cost).strip() for name, cost in by_name.items()}


def test_a_unit_without_a_cost_shows_the_placeholder(
    capsys: pytest.CaptureFixture[str],
) -> None:
    race = races.get_race(RACE)
    free = [unit.name for unit in race.units.values() if unit.cost is None]
    assert free, f"{RACE} is only useful here while some Unit has no Cost"

    _race("units", RACE)
    rows = _rows(capsys.readouterr().out)

    for name in free:
        printed = _cost_of(rows, name)
        assert printed == _plain(_NO_COST).strip()
        assert not any(char.isdigit() for char in printed), name


def test_things_prints_the_three_sections_in_order(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _race("things", RACE)
    out = capsys.readouterr().out
    headers = [line for line in out.splitlines() if _ROW.match(line) is None]

    assert headers == ["Units", "Models", "Equipment"]


def test_things_repeats_each_list_behind_its_header(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _race("units", RACE)
    units = capsys.readouterr().out
    _race("models", RACE)
    models = capsys.readouterr().out
    _race("equipment", RACE)
    equipment = capsys.readouterr().out

    _race("things", RACE)

    assert capsys.readouterr().out == (
        f"Units\n{units}Models\n{models}Equipment\n{equipment}"
    )


@pytest.mark.parametrize("command", ["units", "models", "equipment", "things"])
def test_an_unknown_race_fails_the_way_show_does(command: str) -> None:
    with pytest.raises(cyclopts.CoercionError) as shown:
        _race("show", "nosuchrace")

    with pytest.raises(cyclopts.CoercionError) as listed:
        _race(command, "nosuchrace")

    assert str(listed.value) == str(shown.value)
    assert "nosuchrace" in str(listed.value)
