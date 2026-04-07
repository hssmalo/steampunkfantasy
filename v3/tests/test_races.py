"""Tests for spf.data module."""

import pytest

from spf.races import (
    get_equipments,
    get_metadata,
    get_models,
    get_race,
    get_units,
    list_races,
)
from spf.schemas.race import EquipmentConfig, ModelConfig, RaceMetadata, UnitConfig


def test_list_races_includes_known_races() -> None:
    races = list_races()
    assert "ogre" in races
    assert "goblin" in races
    assert "abomination" in races


def test_list_races_returns_strings() -> None:
    races = list_races()
    assert all(isinstance(name, str) for name in races)


def test_get_race_returns_race_config() -> None:
    race = get_metadata("ogre")
    assert isinstance(race, RaceMetadata)


def test_get_race_ogre_name() -> None:
    race = get_metadata("ogre")
    assert race.name == "Ogre"


def test_get_race_goblin_name() -> None:
    race = get_metadata("goblin")
    assert race.name == "Goblin"


def test_get_race_invalid_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown race"):
        get_metadata("invalid_army")  # type: ignore[arg-type]


def test_get_units_returns_dict_of_unit_configs() -> None:
    units = get_units("ogre")
    assert isinstance(units, dict)
    assert all(isinstance(v, UnitConfig) for v in units.values())


def test_get_units_filters_by_race() -> None:
    # All returned units must belong to the requested army
    units = get_units("ogre")
    assert all(unit.race == "ogre" for unit in units.values())


def test_get_units_not_empty() -> None:
    assert len(get_units("ogre")) > 0


def test_get_models_returns_dict_of_model_configs() -> None:
    models = get_models("ogre")
    assert isinstance(models, dict)
    assert all(isinstance(v, ModelConfig) for v in models.values())


def test_get_models_filters_by_race() -> None:
    models = get_models("ogre")
    assert all(model.race == "ogre" for model in models.values())


def test_get_models_not_empty() -> None:
    assert len(get_models("ogre")) > 0


def test_get_equipments_returns_dict_of_equipment_configs() -> None:
    equipments = get_equipments("ogre")
    assert isinstance(equipments, dict)
    assert all(isinstance(v, EquipmentConfig) for v in equipments.values())


def test_get_equipments_filters_by_race() -> None:
    equipments = get_equipments("ogre")
    assert all(eq.race == "ogre" for eq in equipments.values())


def test_get_equipments_not_empty() -> None:
    assert len(get_equipments("ogre")) > 0


def test_get_army_reexported() -> None:
    # get_race is re-exported from races.py via data.py
    army = get_race("ogre")
    assert army.races["ogre"].name == "Ogre"
