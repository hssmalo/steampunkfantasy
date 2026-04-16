"""Tests for spf.armies.io module."""

import json
from pathlib import Path

import pytest

from spf.armies import Army, ArmyList
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
                equipment=[],
                type=["Infantry"],
                assault=_ASSAULT,
                cost=None,
            ),
        },
        equipment={
            "sword": EquipmentConfig(
                race="goblin",
                name="Sword",
                cost=t.Cost(cp=2),
                upgrade_all=True,
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
    army_list = ArmyList(race="goblin", nick="Test Army", units=())
    save_army(army_list, "test-army")
    loaded = load_army("test-army")
    assert isinstance(loaded, Army)
    assert loaded.race == army_list.race
    assert loaded.units == ()


def test_round_trip_with_units(armies_dir: Path) -> None:  # noqa: ARG001
    race_config = get_race("goblin")
    army_list = ArmyList(race="goblin", nick="Test Army", units=()).add_unit(
        "goblin_infantry", race_config
    )
    save_army(army_list, "goblin-warband")
    loaded = load_army("goblin-warband")
    assert isinstance(loaded, Army)
    assert loaded.race == army_list.race
    assert len(loaded.units) == len(army_list.units)
    assert loaded.units[0].name == army_list.units[0].name
    assert tuple(m.name for m in loaded.units[0].models) == tuple(
        m.name for m in army_list.units[0].models
    )


def test_load_army_returns_resolved_army(armies_dir: Path) -> None:  # noqa: ARG001
    """load_army should return a fully resolved Army, not ArmyList."""
    race_config = get_race("goblin")
    army_list = ArmyList(race="goblin", nick="Test Army", units=()).add_unit(
        "goblin_infantry", race_config
    )
    save_army(army_list, "resolved-test")
    loaded = load_army("resolved-test")
    assert isinstance(loaded, Army)
    # Resolved models have EquipmentConfig objects, not just names
    model = loaded.units[0].models[0]
    assert hasattr(model, "default_equipment")
    assert hasattr(model, "upgrade_equipment")


def test_save_creates_file(armies_dir: Path) -> None:
    army_list = ArmyList(race="goblin", nick="Test Army", units=())
    save_army(army_list, "my-army")
    assert (armies_dir / "my-army.json").exists()


def test_save_creates_parent_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nested = tmp_path / "nested" / "dir"
    monkeypatch.setattr(config.paths, "armies", nested)
    army_list = ArmyList(race="goblin", nick="Test Army", units=())
    save_army(army_list, "my-army")
    assert (nested / "my-army.json").exists()


def test_save_json_contains_race(armies_dir: Path) -> None:
    army_list = ArmyList(race="goblin", nick="Test Army", units=())
    save_army(army_list, "check-race")
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


def test_load_blank_unit_name_raises_value_error(armies_dir: Path) -> None:
    data = {
        "race": "goblin",
        "nick": "Test",
        "units": [{"name": "", "models": []}],
    }
    (armies_dir / "bad-unit.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match=r"Unit #0 \(name ''\): unknown unit name"):
        load_army("bad-unit")


def test_load_blank_model_name_raises_value_error(armies_dir: Path) -> None:
    data = {
        "race": "goblin",
        "nick": "Test",
        "units": [
            {
                "name": "goblin_infantry",
                "models": [{"name": "", "upgrades": []}],
            }
        ],
    }
    (armies_dir / "bad-model.json").write_text(json.dumps(data))
    with pytest.raises(
        ValueError, match=r"Unit #0 \('goblin_infantry'\) / model #0 \(name ''\)"
    ):
        load_army("bad-model")


def test_load_unknown_upgrade_raises_value_error(armies_dir: Path) -> None:
    data = {
        "race": "goblin",
        "nick": "Test",
        "units": [
            {
                "name": "goblin_infantry",
                "models": [
                    {"name": "goblin_infantry", "upgrades": ["no_such_upgrade"]}
                ],
            }
        ],
    }
    (armies_dir / "bad-upgrade.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="unknown equipment 'no_such_upgrade'"):
        load_army("bad-upgrade")


def test_load_multiple_invalid_entries_reported_together(armies_dir: Path) -> None:
    data = {
        "race": "goblin",
        "nick": "Test",
        "units": [
            {"name": "", "models": []},
            {"name": "also_bad", "models": []},
        ],
    }
    (armies_dir / "multi-bad.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="name 'also_bad'") as exc_info:
        load_army("multi-bad")
    msg = str(exc_info.value)
    assert "Unit #0" in msg
    assert "Unit #1" in msg
