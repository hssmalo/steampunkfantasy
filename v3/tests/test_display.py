"""Tests for spf.display module."""

import pytest
from rich.console import Console

from spf.armies.data import Army, add_unit
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
                equipments=[],
                type=["Infantry"],
                assault=_ASSAULT,
                cost=None,
            ),
        },
        equipments={},
    )


def test_print_army_does_not_raise(simple_race: RaceConfig) -> None:
    army = add_unit(Army(race="goblin", units=()), "squad", simple_race)
    # Capture output to avoid noise in test output; assert it runs without error
    console = Console(record=True)
    console.print("")  # prime the recorder
    print_army(army, simple_race)


def test_print_army_empty_army_does_not_raise(simple_race: RaceConfig) -> None:
    army = Army(race="goblin", units=())
    print_army(army, simple_race)
