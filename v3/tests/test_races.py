"""Tests for spf.data module."""

import pytest
from configaroo import Configuration
from pydantic import ValidationError

from spf.config import config as spf_config
from spf.races import (
    get_equipment,
    get_metadata,
    get_models,
    get_race,
    get_units,
    list_races,
)
from spf.schemas.race import (
    EquipmentConfig,
    ModelConfig,
    RaceConfig,
    RaceMetadata,
    UnitConfig,
)


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
        get_metadata("invalid_army")  # pyright: ignore[reportArgumentType]


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


def test_get_equipment_returns_dict_of_equipment_configs() -> None:
    equipment = get_equipment("ogre")
    assert isinstance(equipment, dict)
    assert all(isinstance(v, EquipmentConfig) for v in equipment.values())


def test_get_equipment_filters_by_race() -> None:
    equipment = get_equipment("ogre")
    assert all(eq.race == "ogre" for eq in equipment.values())


def test_get_equipment_not_empty() -> None:
    assert len(get_equipment("ogre")) > 0


def test_get_army_reexported() -> None:
    # get_race is re-exported from races.py via data.py
    army = get_race("ogre")
    assert army.races["ogre"].name == "Ogre"


def _goblin_raw() -> dict:
    """Load goblin.toml as a raw dict (strings, not parsed models)."""
    return Configuration.from_file(spf_config.paths.races / "goblin.toml").to_dict()


def test_spawn_validation_invalid_unit() -> None:
    # Load a valid config from TOML (BeforeValidator fields are still raw strings)
    config_dict = _goblin_raw()

    # Mutate to point to an invalid unit in spawns
    config_dict["spawns"]["tiny_snake"]["unit"] = "invalid_unit_name"

    with pytest.raises(
        ValidationError,
        match="Spawn 'tiny_snake' references invalid unit 'invalid_unit_name'",
    ):
        RaceConfig.model_validate(config_dict)


def test_spawn_validation_invalid_equipment() -> None:
    config_dict = _goblin_raw()

    # Add an invalid equipment to the spawn config
    config_dict["spawns"]["tiny_snake"]["equipment"] = ["invalid_eq"]

    with pytest.raises(
        ValidationError,
        match="Spawn 'tiny_snake' references invalid equipment 'invalid_eq'",
    ):
        RaceConfig.model_validate(config_dict)


def test_spawn_rule_invalid_format() -> None:
    config_dict = _goblin_raw()

    # Change the Spawn special rule to have no colon
    config_dict["equipment"]["snake_arrows"]["range"]["special"]["Spawn"] = (
        "Place one hidden tiny snake"
    )

    with pytest.raises(
        ValidationError,
        match="must follow the format '\\[spawn_id\\]: \\[placement_text\\]'",
    ):
        RaceConfig.model_validate(config_dict)


def test_spawn_rule_undefined_spawn_id() -> None:
    config_dict = _goblin_raw()

    # Reference an undefined spawn ID
    config_dict["equipment"]["snake_arrows"]["range"]["special"]["Spawn"] = (
        "unknown_spawn: Place one hidden tiny snake"
    )

    with pytest.raises(
        ValidationError,
        match="references undefined spawn ID 'unknown_spawn'",
    ):
        RaceConfig.model_validate(config_dict)
