"""Tests for spf.display module."""

import pytest
from rich.console import Console

import spf.armies.io
from spf.armies import ArmyList
from spf.armies.io import print_army
from spf.schemas import type_aliases as t
from spf.schemas.race import (
    AssaultConfig,
    ModelConfig,
    OrdersConfig,
    RaceConfig,
    RaceMetadata,
    ShakenConfig,
    UnitConfig,
)

_ASSAULT = AssaultConfig(
    strength=[1, 0, 0, 0],
    strength_die="4+",
    deflection=[1, 0, 0, 0],
    deflection_die="4+",
    damage="d4",
    ap=0,
)


@pytest.fixture
def simple_race() -> RaceConfig:
    """Minimal RaceConfig for display tests."""
    return RaceConfig(
        races={"goblin": RaceMetadata(name="Goblin")},
        units={
            "squad": UnitConfig(
                race="goblin",
                name="Squad",
                models=["soldier"],
                size="Small",
                cost=t.Cost(mp=3),
                shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
                special={},
                orders=OrdersConfig(),
                armor=None,
                damage_tables={"regular": ["Fine", "Dead"]},
            )
        },
        models={
            "soldier": ModelConfig(
                race="goblin",
                name="Soldier",
                equipment_limit=["Hands:2"],  # pyright: ignore[reportArgumentType]
                equipment=[],
                type=["Infantry"],
                assault=_ASSAULT,
                cost=None,
            ),
        },
        equipment={},
    )


def test_print_army_does_not_raise(simple_race: RaceConfig) -> None:
    army = (
        ArmyList(race="goblin", nick="Test Army", units=())
        .add_unit("squad", simple_race)
        .resolve(simple_race)
    )
    console = Console(record=True)
    console.print("")
    print_army(army)


def test_print_army_empty_army_does_not_raise(simple_race: RaceConfig) -> None:
    army = ArmyList(race="goblin", nick="Test Army", units=()).resolve(simple_race)
    print_army(army)


def test_print_army_unit_line_includes_points(
    simple_race: RaceConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    capture = Console(record=True)
    monkeypatch.setattr(spf.armies.io, "stdout", capture)

    army = (
        ArmyList(race="goblin", nick="Test Army", units=())
        .add_unit("squad", simple_race)
        .resolve(simple_race)
    )
    print_army(army)

    output = capture.export_text()
    # squad costs mp=3, points = 3
    assert "Squad (3 pts)" in output
