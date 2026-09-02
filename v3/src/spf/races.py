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
            and (not validate or race_load_error(race) is None)
        )
    ]


def race_load_error(race_name: t.RaceName) -> pydantic.ValidationError | None:
    """Return why a Race will not load, or None when it loads.

    The whole error rather than a message: `spf lint races` reports one Load
    finding per pydantic error, which a flattened string cannot carry.
    """
    try:
        get_race(race_name)
    except pydantic.ValidationError as err:
        return err
    else:
        return None


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
