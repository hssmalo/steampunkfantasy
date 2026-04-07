"""Data access functions for SteamPunkFantasy armies."""

from configaroo import Configuration

from spf.config import config
from spf.schemas import type_aliases as t
from spf.schemas.army import (
    ArmyConfig,
    EquipmentConfig,
    ModelConfig,
    RaceConfig,
    UnitConfig,
)


def list_armies() -> list[str]:
    """List army names available in the data directory."""
    return [path.stem for path in sorted(config.paths.data.glob("*.toml"))]


def get_army(army_name: t.ArmyName) -> ArmyConfig:
    """Get the definition of one army."""
    path = config.paths.data / f"{army_name}.toml"
    return Configuration.from_file(path).convert_model(ArmyConfig)


def get_race(army_name: t.ArmyName) -> RaceConfig:
    """Get race metadata for a given army."""
    available = list_armies()
    if army_name not in available:
        raise ValueError(
            f"Unknown army {army_name!r}. Available armies: {', '.join(available)}"
        )
    army = get_army(army_name)
    return army.races[army_name]


def get_units(army_name: t.ArmyName) -> dict[str, UnitConfig]:
    """Get all units belonging to the given army."""
    army = get_army(army_name)
    return {k: v for k, v in army.units.items() if v.race == army_name}


def get_models(army_name: t.ArmyName) -> dict[str, ModelConfig]:
    """Get all models belonging to the given army."""
    army = get_army(army_name)
    return {k: v for k, v in army.models.items() if v.race == army_name}


def get_equipments(army_name: t.ArmyName) -> dict[str, EquipmentConfig]:
    """Get all equipment belonging to the given army."""
    army = get_army(army_name)
    return {k: v for k, v in army.equipments.items() if v.race == army_name}
