"""Tests for spf.data module."""

import pytest

from spf.armies import (
    get_army,
    get_equipments,
    get_models,
    get_race,
    get_units,
    list_armies,
)
from spf.schemas.army import EquipmentConfig, ModelConfig, RaceConfig, UnitConfig


def test_list_armies_includes_known_armies() -> None:
    armies = list_armies()
    assert "ogre" in armies
    assert "goblin" in armies
    assert "abomination" in armies


def test_list_armies_returns_strings() -> None:
    armies = list_armies()
    assert all(isinstance(name, str) for name in armies)


def test_get_race_returns_race_config() -> None:
    race = get_race("ogre")
    assert isinstance(race, RaceConfig)


def test_get_race_ogre_name() -> None:
    race = get_race("ogre")
    assert race.name == "Ogre"


def test_get_race_goblin_name() -> None:
    race = get_race("goblin")
    assert race.name == "Goblin"


def test_get_race_invalid_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown army"):
        get_race("invalid_army")  # type: ignore[arg-type]


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
    # get_army is re-exported from armies.py via data.py
    army = get_army("ogre")
    assert army.races["ogre"].name == "Ogre"
