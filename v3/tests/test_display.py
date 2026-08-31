"""Tests for spf.display module."""

import pytest
from rich.console import Console

import spf.armies.io
from spf.armies.io import print_army
from spf.schemas.race import RaceConfig
from tests.conftest import synthetic_army, synthetic_race


@pytest.fixture
def simple_race() -> RaceConfig:
    """Return the default synthetic Race; printing an Army asks nothing more."""
    return synthetic_race()


def test_print_army_does_not_raise(simple_race: RaceConfig) -> None:
    army = synthetic_army(simple_race).resolve(simple_race)
    console = Console(record=True)
    console.print("")
    print_army(army)


def test_print_army_empty_army_does_not_raise(simple_race: RaceConfig) -> None:
    army = synthetic_army(simple_race, units=[]).resolve(simple_race)
    print_army(army)


def test_print_army_unit_line_includes_points(
    simple_race: RaceConfig, *, monkeypatch: pytest.MonkeyPatch
) -> None:
    capture = Console(record=True)
    monkeypatch.setattr(spf.armies.io, "stdout", capture)

    army = synthetic_army(simple_race).resolve(simple_race)
    print_army(army)

    output = capture.export_text()
    # squad costs mp=3, points = 3
    assert "Squad" in output
    assert "(3 pts)" in output


def test_print_army_model_line_shows_display_name_not_toml_key(
    simple_race: RaceConfig, *, monkeypatch: pytest.MonkeyPatch
) -> None:
    capture = Console(record=True)
    monkeypatch.setattr(spf.armies.io, "stdout", capture)

    army = synthetic_army(simple_race).resolve(simple_race)
    print_army(army)

    output = capture.export_text()
    assert "Soldier" in output
    assert "soldier" not in output


def test_print_army_shows_unit_and_model_nicks(
    simple_race: RaceConfig, *, monkeypatch: pytest.MonkeyPatch
) -> None:
    capture = Console(record=True)
    monkeypatch.setattr(spf.armies.io, "stdout", capture)

    army = (
        synthetic_army(simple_race, units=[])
        .add_unit("squad", nick="Da Lads", race_config=simple_race)
        .nick_model(("squad", 0), model_key=("soldier", 0), nick="Grubnak")
        .resolve(simple_race)
    )
    print_army(army)

    output = capture.export_text()
    assert "Da Lads" in output
    assert "Grubnak" in output
    assert "Squad" not in output
    assert "Soldier" not in output
