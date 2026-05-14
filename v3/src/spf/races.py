"""Data access functions for SteamPunkFantasy races."""

from typing import cast

import pydantic
from configaroo import Configuration

from spf.config import config
from spf.schemas import race as r
from spf.schemas import type_aliases as t


def list_races(*, validate: bool = False) -> list[t.RaceName]:
    """List race names available in the data directory."""
    return [
        race
        for path in sorted(config.paths.races.glob("*.toml"))
        if (
            (race := cast("t.RaceName", path.stem))
            and (not validate or _race_validates(race))
        )
    ]


def _race_validates(race_name: t.RaceName) -> bool:
    """Check if the TOML definition of a race validates."""
    try:
        get_race(race_name)
    except pydantic.ValidationError:
        return False
    else:
        return True


def get_race(race: t.RaceName) -> r.RaceConfig:
    """Get the definition of one race."""
    try:
        path = config.paths.races / f"{race}.toml"
        return Configuration.from_file(path).convert_model(r.RaceConfig)
    except FileNotFoundError:
        available = ", ".join(list_races())
        msg = f"Unknown race '{race}'. Available races: {available}"
        raise ValueError(msg) from None


def get_metadata(race: t.RaceName) -> r.RaceMetadata:
    """Get race metadata for a given race."""
    return get_race(race).races[race]


def get_units(race: t.RaceName) -> dict[t.UnitName, r.UnitConfig]:
    """Get all units belonging to the given race."""
    return get_race(race).units


def get_models(race: t.RaceName) -> dict[t.ModelName, r.ModelConfig]:
    """Get all models belonging to the given race."""
    return get_race(race).models


def get_equipment(race: t.RaceName) -> dict[t.EquipmentName, r.EquipmentConfig]:
    """Get all equipment belonging to the given race."""
    return get_race(race).equipment
