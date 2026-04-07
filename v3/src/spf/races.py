"""Data access functions for SteamPunkFantasy races."""

from typing import cast

from configaroo import Configuration

from spf.config import config
from spf.schemas import race as r
from spf.schemas import type_aliases as t


def list_races() -> list[t.RaceName]:
    """List race names available in the data directory."""
    return [
        cast("t.RaceName", path.stem)
        for path in sorted(config.paths.data.glob("*.toml"))
    ]


def get_race(race: t.RaceName) -> r.RaceConfig:
    """Get the definition of one race."""
    try:
        path = config.paths.data / f"{race}.toml"
        return Configuration.from_file(path).convert_model(r.RaceConfig)
    except FileNotFoundError:
        available = ", ".join(list_races())
        msg = f"Unknown race '{race}'. Available races: {available}"
        raise ValueError(msg)


def get_metadata(race: t.RaceName) -> r.RaceMetadata:
    """Get race metadata for a given race."""
    return get_race(race).races[race]


def get_units(race: t.RaceName) -> dict[t.UnitName, r.UnitConfig]:
    """Get all units belonging to the given race."""
    return get_race(race).units


def get_models(race: t.RaceName) -> dict[t.ModelName, r.ModelConfig]:
    """Get all models belonging to the given race."""
    return get_race(race).models


def get_equipments(race: t.RaceName) -> dict[t.EquipmentName, r.EquipmentConfig]:
    """Get all equipment belonging to the given race."""
    return get_race(race).equipments
