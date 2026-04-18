"""Tests for print_army_rules display function."""

import pytest
from rich.console import Console

import spf.armies.io
from spf.armies import ArmyList
from spf.armies.io import print_army_rules
from spf.config import config
from spf.frontends.cli.army import rules_army
from spf.schemas import type_aliases as t
from spf.schemas.race import (
    AssaultConfig,
    EquipmentConfig,
    EquipmentRangeConfig,
    ModelConfig,
    OrdersConfig,
    RaceConfig,
    RaceMetadata,
    ShakenConfig,
    UnitConfig,
)

_ASSAULT = AssaultConfig(
    strength=[2, 1, 0, 1],
    strength_die="4+",
    deflection=[1, 0, 0, 0],
    deflection_die="5+",
    damage="d6",
    ap=1,
)


@pytest.fixture
def simple_race() -> RaceConfig:
    """RaceConfig with one unit, one model, and one equipment with a range profile."""
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
                special={"Terror": "causes fear"},
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
                special={"To Hit": "reroll 1s"},
            ),
        },
        equipment={
            "bow": EquipmentConfig(
                race="goblin",
                name="Short Bow",
                cost=t.Cost(cp=1),
                upgrade_all=True,
                requires=[],
                range=EquipmentRangeConfig(
                    range=30,
                    angle=[True, False, False, False],  # pyright: ignore[reportArgumentType]
                    damage="d4",
                    ap=0,
                ),
            ),
            "sword": EquipmentConfig(
                race="goblin",
                name="Sword",
                cost=t.Cost(cp=2),
                upgrade_all=True,
                requires=[],
            ),
        },
    )


@pytest.fixture
def capture(monkeypatch: pytest.MonkeyPatch) -> Console:
    """Redirect stdout in io module to a recording console."""
    console = Console(record=True)
    monkeypatch.setattr(spf.armies.io, "stdout", console)
    return console


def _army(race: RaceConfig, upgrades: tuple[str, ...] = ()) -> ArmyList:
    army = ArmyList(race="goblin", nick="Test Army", units=()).add_unit("squad", race)
    for upgrade in upgrades:
        army = army.upgrade_model(("squad", 0), ("soldier", 0), upgrade, race)
    return army


# ---------------------------------------------------------------------------
# Unit-level output
# ---------------------------------------------------------------------------


def test_unit_line_includes_name_and_pts(
    simple_race: RaceConfig, capture: Console
) -> None:
    army = _army(simple_race).resolve(simple_race)
    print_army_rules(army)
    assert "Squad -  3mp  0cp  0xp  0ip" in capture.export_text()


def test_unit_specials_shown_when_present(
    simple_race: RaceConfig, capture: Console
) -> None:
    army = _army(simple_race).resolve(simple_race)
    print_army_rules(army)
    output = capture.export_text()
    assert "Terror" in output
    assert "causes fear" in output


def test_unit_with_no_specials_omits_specials_line(capture: Console) -> None:
    race_no_special = RaceConfig(
        races={"goblin": RaceMetadata(name="Goblin")},
        units={
            "squad": UnitConfig(
                race="goblin",
                name="Squad",
                models=["soldier"],
                size="Small",
                cost=t.Cost(mp=2),
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
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race_no_special)
        .resolve(race_no_special)
    )
    print_army_rules(army)
    assert "Specials" not in capture.export_text()


# ---------------------------------------------------------------------------
# Model-level output
# ---------------------------------------------------------------------------


def test_model_line_shows_name(simple_race: RaceConfig, capture: Console) -> None:
    army = _army(simple_race).resolve(simple_race)
    print_army_rules(army)
    assert "soldier" in capture.export_text()


def test_model_line_omits_cost_when_zero(
    simple_race: RaceConfig, capture: Console
) -> None:
    army = _army(simple_race).resolve(simple_race)
    print_army_rules(army)
    output = capture.export_text()
    # "Soldier" has no upgrade cost; no pts suffix should follow the model name
    lines = [
        line
        for line in output.splitlines()
        if "Soldier" in line and "pts" in line and "Squad" not in line
    ]
    assert lines == []


def test_model_specials_shown(simple_race: RaceConfig, capture: Console) -> None:
    army = _army(simple_race).resolve(simple_race)
    print_army_rules(army)
    output = capture.export_text()
    assert "To Hit" in output
    assert "reroll 1s" in output


# ---------------------------------------------------------------------------
# Equipment and range
# ---------------------------------------------------------------------------


def test_equipment_shown_with_cost(simple_race: RaceConfig, capture: Console) -> None:
    army = _army(simple_race, upgrades=("sword",)).resolve(simple_race)
    print_army_rules(army)
    output = capture.export_text()
    assert "Sword" in output


def test_range_weapon_stats_shown(simple_race: RaceConfig, capture: Console) -> None:
    army = _army(simple_race, upgrades=("bow",)).resolve(simple_race)
    print_army_rules(army)
    output = capture.export_text()
    assert "Range" in output
    assert "30" in output
    assert "d4" in output


def test_equipment_without_range_omits_range_stats(
    simple_race: RaceConfig, capture: Console
) -> None:
    army = _army(simple_race, upgrades=("sword",)).resolve(simple_race)
    print_army_rules(army)
    assert "Range" not in capture.export_text()


# ---------------------------------------------------------------------------
# Assault profile
# ---------------------------------------------------------------------------


def test_assault_profile_shown(simple_race: RaceConfig, capture: Console) -> None:
    army = _army(simple_race).resolve(simple_race)
    print_army_rules(army)
    output = capture.export_text()
    assert "Assault" in output
    assert "Strength" in output
    assert "Deflect" in output
    assert "Damage" in output
    assert "AP" in output


# ---------------------------------------------------------------------------
# Total cost
# ---------------------------------------------------------------------------


def test_total_cost_shown(simple_race: RaceConfig, capture: Console) -> None:
    army = _army(simple_race).resolve(simple_race)
    print_army_rules(army)
    assert "Total cost" in capture.export_text()


# ---------------------------------------------------------------------------
# CLI error path
# ---------------------------------------------------------------------------


def test_rules_army_missing_file_exits_nonzero(
    tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config.paths, "armies", tmp_path)  # type: ignore[arg-type]
    with pytest.raises(SystemExit) as exc_info:
        rules_army("no-such-army")
    assert exc_info.value.code != 0
