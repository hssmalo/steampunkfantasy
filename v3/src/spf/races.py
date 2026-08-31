"""Data access functions for SteamPunkFantasy races."""

from collections.abc import Iterator
from typing import cast

import pydantic
from configaroo import Configuration

from spf.config import config
from spf.schemas import race as r
from spf.schemas import type_aliases as t
from spf.schemas.special import Specials


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


def special_slots(race: r.RaceConfig) -> Iterator[tuple[str, str, Specials]]:
    """Every (section, key, instances) triple a Race hangs Specials off.

    Which slots a holder has is the holder's own shape: only Equipment carries
    a range profile, and only a Model an assault one it always has. One walk
    rather than one per consumer, so a new slot is added in a single place.
    """
    for key, unit in race.units.items():
        yield "units", key, unit.specials
    for key, model in race.models.items():
        yield "models", key, model.unit_specials
        yield "models", key, model.specials
        yield "models", key, model.assault.specials
    for key, equipment in race.equipment.items():
        yield "equipment", key, equipment.unit_specials
        yield "equipment", key, equipment.model_specials
        if equipment.assault is not None:
            yield "equipment", key, equipment.assault.specials
        if equipment.range is not None:
            yield "equipment", key, equipment.range.specials
