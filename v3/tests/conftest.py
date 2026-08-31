"""Test-suite-wide setup.

Pytest imports this before any test module, and therefore before
`spf.console` constructs its Rich Consoles — which is what makes the
environment pinning below effective. A Console reads its color and width
settings once, at construction, so none of this works as a fixture.
"""

import os

# Rich emits color and bold when FORCE_COLOR is set, and those escapes land in
# `capsys` output — where a test asserting on layout sees `'\x1b[32m4.1'`
# instead of `'4.1'`. Some terminals, CI runners and agent harnesses set it.
# These tests assert on text, not styling, so the suite runs uncolored.
for _var in ("FORCE_COLOR", "COLORTERM"):
    os.environ.pop(_var, None)
os.environ["TERM"] = "dumb"

# `SPF_` is the project's namespace: `spf.config`, `spf.rules` and `spf.armies.io`
# all fold `SPF_`-prefixed variables into their Configuration at import, so any
# exported one can decide what the suite resolves against — a contributor's
# `SPF_COMFYUI_ENV=cloud` picked the Environment for the whole run. Clearing the
# namespace wholesale keeps that true of variables added later, which an explicit
# list would not. Tests pin what they need on `config`, or set their own vars
# through `monkeypatch` after this has run; the ambient ones are not theirs.
for _var in [_name for _name in os.environ if _name.startswith("SPF_")]:
    os.environ.pop(_var, None)

# Rich otherwise takes its width from the invoking terminal, so where a message
# wraps depends on the window the suite happens to be run from. Pinning it makes
# a run reproducible — but it is deliberately *not* what makes these tests pass:
# they are green with this line deleted at every width from 40 to 250, because
# the ones that match on a message compare it `unwrapped`. Keep it that way. A
# test that only passes at 100 is a test that will fail on someone's laptop.
os.environ["COLUMNS"] = "100"

# Everything below imports `spf`, and therefore has to be imported *after* the
# scrubbing above: `spf.config` folds the `SPF_` namespace into its
# Configuration at import time, and `spf.console` reads the color and width
# settings once, when its Consoles are constructed.
from pathlib import Path  # noqa: E402
from typing import cast  # noqa: E402

import tomli_w  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from spf.schemas import type_aliases as t  # noqa: E402
from spf.schemas.race import (  # noqa: E402
    EquipmentConfig,
    ModelConfig,
    RaceConfig,
    RaceMetadata,
    SpawnConfig,
    UnitConfig,
)


def unwrapped(text: str) -> str:
    """Collapse Rich's line breaks so a message can be matched as one string.

    Rich wraps console output to the terminal width, and the break can land
    inside the very phrase a test is looking for, splitting "does not support
    refinement" across two lines. Where the subject is *that the message
    reached the user*, rather than how it was laid out, assert against this
    instead of the raw capture.
    """
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Synthetic Race builders
# ---------------------------------------------------------------------------
#
# Shared stand-ins for the committed corpus (ADR 0033). Each builder takes the
# fields a Race file writes and fills the rest in, so a test spells out only
# what it is about. They are builders rather than fixtures because tests vary
# too much for one frozen Race: each test shapes its own, and no single fixture
# grows a flag per caller.

_RACE: t.RaceName = "goblin"
"""The Race every builder belongs to. A `RaceName` is a closed set, so a
synthetic Race borrows a real name and nothing else."""


def synthetic_unit(**fields: object) -> UnitConfig:
    """Build a Unit, filling in every field a Race file has to supply.

    Costed by default, since an uncosted Unit is the special case.
    """
    return UnitConfig.model_validate(
        {
            "race": _RACE,
            "name": "Squad",
            "models": ["soldier"],
            "size": "small",
            "cost": {"mp": 3},
            "shaken": {"speed": "slow", "movement_order": ["-", "-", "flee"]},
            "orders": {},
            "damage_tables": {"Regular": {"rows": ["1: Fine", "2: Dead"]}},
        }
        | fields
    )


def synthetic_model(
    *, holders: list[str] | None = None, **fields: object
) -> ModelConfig:
    """Build a Model. `holders` names its Holders and their capacity, 'Hands:2'."""
    return ModelConfig.model_validate(
        {
            "race": _RACE,
            "name": "Soldier",
            "equipment_limit": holders if holders is not None else ["Hands:2"],
            "equipment": ["knife"],
            "type": ["Infantry"],
            "assault": {
                "strength": [1, 0, 0, 0],
                "strength_die": "4+",
                "deflection": [1, 0, 0, 0],
                "deflection_die": "4+",
                "damage": "d4",
                "ap": 0,
            },
        }
        | fields
    )


def synthetic_equipment(**fields: object) -> EquipmentConfig:
    """Build an Upgrade Equipment. Pass `cost=None, upgrade_all=None` for a Default."""
    return EquipmentConfig.model_validate(
        {
            "race": _RACE,
            "name": "Sword",
            "cost": {"cp": 2},
            "upgrade_all": True,
            "requires": [["Hands:1"]],
        }
        | fields
    )


def synthetic_race(
    *,
    units: dict[str, UnitConfig] | None = None,
    models: dict[str, ModelConfig] | None = None,
    equipment: dict[str, EquipmentConfig] | None = None,
    spawns: dict[str, SpawnConfig] | None = None,
) -> RaceConfig:
    """Build a Race, by default a costed and an uncosted Unit of one Model.

    The Model declares one Holder and carries one Default Equipment; one
    Upgrade Equipment is on the shelf for it.
    """
    return RaceConfig(
        races={_RACE: RaceMetadata(name="Goblin")},
        units=units
        if units is not None
        else {
            "squad": synthetic_unit(),
            "mob": synthetic_unit(name="Mob", cost=None),
        },
        models=models if models is not None else {"soldier": synthetic_model()},
        equipment=equipment
        if equipment is not None
        else {
            "knife": synthetic_equipment(name="Knife", cost=None, upgrade_all=None),
            "sword": synthetic_equipment(),
        },
        spawns=spawns if spawns is not None else {},
    )


def write_race_toml(directory: Path, race: RaceConfig) -> Path:
    """Write a Race out as the TOML file `spf.races` reads, and return its path.

    For a test that needs a Race on disk rather than in memory; point
    `config.paths.races` at the directory to load it back.
    """
    path = directory / f"{next(iter(race.races))}.toml"
    path.write_text(tomli_w.dumps(cast("dict[str, object]", _toml_ready(race))))
    return path


def _toml_ready(value: object) -> object:
    """Restore the written form of every field a Race file spells as a string.

    A parsed `EquipmentLimit`, `Requirement` or `DamageRow` dumps as the model
    it became, which the loader's parsers then reject; each goes back to the
    one-line form the data is authored in. Unset fields are dropped rather than
    written as null, which TOML has no spelling for.
    """
    match value:
        case t.EquipmentLimit():
            text = f"{value.holder}:{value.limit}"
        case t.Requirement():
            text = f"{value.key}:{value.value}"
        case t.DamageRow():
            text = f"{_roll(value.roll)}: {value.effect}"
        case BaseModel():
            return {
                name: _toml_ready(field) for name, field in value if field is not None
            }
        case dict():
            return {key: _toml_ready(item) for key, item in value.items()}
        case list():
            return [_toml_ready(item) for item in value]
        case _:
            return value
    return text


def _roll(roll: t.DamageRoll) -> str:
    """Spell a damage roll the way a damage-table row writes it."""
    match roll:
        case t.RangeRoll():
            return f"{roll.low}-{roll.high}"
        case t.AtLeastRoll():
            return f"{roll.value}+"
        case t.ExactRoll():
            return str(roll.value)
