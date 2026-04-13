"""Tests for spf.armies.io module."""

import json
from pathlib import Path

import pytest

from spf.armies.data import Army, add_unit
from spf.armies.io import load_army, save_army
from spf.config import config
from spf.races import get_race
from spf.schemas import type_aliases as t
from spf.schemas.race import (
    AssaultConfig,
    EquipmentConfig,
    ModelConfig,
    OrdersConfig,
    RaceConfig,
    RaceMetadata,
    ShakenConfig,
    UnitConfig,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
    """Minimal RaceConfig with one unit and one model."""
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
        equipments={
            "sword": EquipmentConfig(
                race="goblin",
                name="Sword",
                cost=t.Cost(cp=2),
                requires=[["Hands:1"], ["type:Infantry"]],  # pyright: ignore[reportArgumentType]
            ),
        },
    )


@pytest.fixture
def armies_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect config.paths.armies to a temporary directory."""
    monkeypatch.setattr(config.paths, "armies", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# save_army / load_army round-trip
# ---------------------------------------------------------------------------


def test_round_trip_empty_army(armies_dir: Path) -> None:  # noqa: ARG001
    army = Army(race="goblin", nick="Test Army", units=())
    save_army(army, "test-army")
    loaded = load_army("test-army")
    assert loaded.race == army.race
    assert loaded.units == ()


def test_round_trip_with_units(armies_dir: Path) -> None:  # noqa: ARG001
    race_config = get_race("goblin")
    army = add_unit(
        Army(race="goblin", nick="Test Army", units=()), "goblin_infantry", race_config
    )
    save_army(army, "goblin-warband")
    loaded = load_army("goblin-warband")
    assert loaded.race == army.race
    assert len(loaded.units) == len(army.units)
    assert loaded.units[0].name == army.units[0].name
    assert tuple(m.name for m in loaded.units[0].models) == tuple(
        m.name for m in army.units[0].models
    )


def test_save_creates_file(armies_dir: Path) -> None:
    army = Army(race="goblin", nick="Test Army", units=())
    save_army(army, "my-army")
    assert (armies_dir / "my-army.json").exists()


def test_save_creates_parent_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nested = tmp_path / "nested" / "dir"
    monkeypatch.setattr(config.paths, "armies", nested)
    army = Army(race="goblin", nick="Test Army", units=())
    save_army(army, "my-army")
    assert (nested / "my-army.json").exists()


def test_save_json_contains_race(armies_dir: Path) -> None:
    army = Army(race="goblin", nick="Test Army", units=())
    save_army(army, "check-race")
    data = json.loads((armies_dir / "check-race.json").read_text())
    assert data["race"] == "goblin"


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_load_missing_army_raises_file_not_found(armies_dir: Path) -> None:  # noqa: ARG001
    with pytest.raises(FileNotFoundError, match="no-such-army"):
        load_army("no-such-army")


def test_load_unknown_race_raises_value_error(armies_dir: Path) -> None:
    (armies_dir / "bad-race.json").write_text(
        json.dumps({"race": "nonexistent_race_xyz", "units": []})
    )
    with pytest.raises(ValueError, match="nonexistent_race_xyz"):
        load_army("bad-race")
