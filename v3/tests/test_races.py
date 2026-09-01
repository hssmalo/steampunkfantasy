"""Tests for spf.data module."""

from pathlib import Path

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
    race_load_error,
)
from spf.schemas.race import (
    RaceConfig,
    RaceMetadata,
    _validate_specials,
)
from spf.schemas.special import SpecialInstance
from tests.conftest import InstallRegistry, synthetic_race, write_race_toml


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


def test_get_units_filters_by_race() -> None:
    # All returned units must belong to the requested army
    units = get_units("ogre")
    assert all(unit.race == "ogre" for unit in units.values())


def test_get_models_filters_by_race() -> None:
    models = get_models("ogre")
    assert all(model.race == "ogre" for model in models.values())


def test_get_models_not_empty() -> None:
    assert len(get_models("ogre")) > 0


def test_get_equipment_filters_by_race() -> None:
    equipment = get_equipment("ogre")
    assert all(eq.race == "ogre" for eq in equipment.values())


def test_get_equipment_not_empty() -> None:
    assert len(get_equipment("ogre")) > 0


def test_get_army_reexported() -> None:
    # get_race is re-exported from races.py via data.py
    army = get_race("ogre")
    assert army.races["ogre"].name == "Ogre"


# ---------------------------------------------------------------------------
# race_load_error
# ---------------------------------------------------------------------------


def test_race_load_error_is_none_for_a_race_that_loads(
    races_dir: Path, install_registry: InstallRegistry
) -> None:
    """A Race with nothing wrong with it reports nothing."""
    install_registry()
    write_race_toml(races_dir, synthetic_race())

    assert race_load_error("goblin") is None


def test_race_load_error_returns_the_validation_error(races_dir: Path) -> None:
    """A Race that will not load hands back why, rather than a bare False."""
    (races_dir / "ork.toml").write_text("[races.ork]\nname = 123\n")

    error = race_load_error("ork")

    assert isinstance(error, ValidationError)


def test_race_load_error_carries_every_pydantic_error(races_dir: Path) -> None:
    """The whole error survives, so a caller can report one line per problem."""
    (races_dir / "ork.toml").write_text("[races.ork]\nname = 123\nversion = 456\n")

    error = race_load_error("ork")

    assert error is not None
    assert len(error.errors()) > 1


def test_list_races_validate_drops_a_race_that_will_not_load(
    races_dir: Path, install_registry: InstallRegistry
) -> None:
    """`validate=True` still filters, now by asking `race_load_error`."""
    install_registry()
    write_race_toml(races_dir, synthetic_race())
    (races_dir / "ork.toml").write_text("[races.ork]\nname = 123\n")

    assert list_races() == ["goblin", "ork"]
    assert list_races(validate=True) == ["goblin"]


def _goblin_raw() -> dict:
    """Load goblin.toml as a raw dict (strings, not parsed models)."""
    return Configuration.from_file(spf_config.paths.races / "goblin.toml").to_dict()


def _gnome_raw() -> dict:
    """Load gnome.toml as a raw dict (strings, not parsed models)."""
    return Configuration.from_file(spf_config.paths.races / "gnome.toml").to_dict()


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
    config_dict = _gnome_raw()

    # Change the Spawn instance's text so it names no spawn at all
    config_dict["equipment"]["assault_bot_mortar"]["range"]["specials"]["spawn"] = [
        {"text": "Place one hidden tiny snake"}
    ]

    with pytest.raises(
        ValidationError,
        match="must follow the format '\\[spawn_id\\]: \\[placement_text\\]'",
    ):
        RaceConfig.model_validate(config_dict)


def test_spawn_rule_rejects_a_variant() -> None:
    # A spawning rule names its spawn in its own prose, and the variant pool
    # lives in a registry this validator does not have. Checked here rather
    # than through a whole Race: no spawning rule defines a variant today, so
    # the registry gate would reject the id before this rule ever saw it.
    specials = {"spawn": [SpecialInstance(variant="place_a_tiny_snake")]}

    with pytest.raises(ValueError, match="cannot draw prose from a variant"):
        _validate_specials({"tiny_snake"}, specials, context="equipment 'Mortar'")


def test_spawn_rule_undefined_spawn_id() -> None:
    config_dict = _gnome_raw()

    # Reference an undefined spawn ID
    config_dict["equipment"]["assault_bot_mortar"]["range"]["specials"]["spawn"] = [
        {"text": "unknown_spawn: Place one assault bot"}
    ]

    with pytest.raises(
        ValidationError,
        match="references undefined spawn ID 'unknown_spawn'",
    ):
        RaceConfig.model_validate(config_dict)
