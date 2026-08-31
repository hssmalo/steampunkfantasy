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
import sys  # noqa: E402
from collections.abc import Callable, Mapping  # noqa: E402
from pathlib import Path  # noqa: E402
from types import ModuleType  # noqa: E402
from typing import cast  # noqa: E402

import pytest  # noqa: E402
import tomli_w  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from spf import registry as reg  # noqa: E402
from spf.armies import ArmyList  # noqa: E402
from spf.config import config  # noqa: E402
from spf.schemas import rules as r  # noqa: E402
from spf.schemas import type_aliases as t  # noqa: E402
from spf.schemas.race import (  # noqa: E402
    AssaultConfig,
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


def synthetic_assault(**fields: object) -> AssaultConfig:
    """Build a Model's assault stats, the block every Model has to carry."""
    return AssaultConfig.model_validate(
        {
            "strength": [1, 0, 0, 0],
            "strength_die": "4+",
            "deflection": [1, 0, 0, 0],
            "deflection_die": "4+",
            "damage": "d4",
            "ap": 0,
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
            "assault": synthetic_assault(),
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


def synthetic_army(
    race: RaceConfig, *, units: list[str] | None = None, nick: str = "Test Army"
) -> ArmyList:
    """Field an Army of the named Units, drawn from the given Race.

    Unresolved, the way a player's Army is while it is being built: call
    `.resolve(race)` for the Army the renderings read.
    """
    army = ArmyList(race=next(iter(race.races)), nick=nick, units=[])
    for name in units if units is not None else ["squad"]:
        army = army.add_unit(name, race_config=race)
    return army


@pytest.fixture
def armies_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point `config.paths.armies` at a directory of this test's own.

    The committed Armies are a subject in their own right; a test about
    saving, listing or loading is not about them.
    """
    monkeypatch.setattr(config.paths, "armies", tmp_path)
    return tmp_path


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


# ---------------------------------------------------------------------------
# Synthetic Registries, and the seam that installs one
# ---------------------------------------------------------------------------
#
# A Race's Special ids, Sizes and Speeds are resolved against the registries
# when it loads (ADR 0024), so a synthetic Race is only as free as the registry
# it is checked against. Installing one is what lets a test invent the ids it
# needs instead of borrowing a committed Race that happens to use them.


def synthetic_special(**fields: object) -> r.SpecialRuleConfig:
    """Build a Special rule, permitting every Slot unless `slots` narrows it."""
    return r.SpecialRuleConfig.model_validate(
        {
            "name": "Special",
            "slots": ["unit", "model", "assault", "range"],
            "effect": "Does something.",
        }
        | fields
    )


def synthetic_registry(
    *,
    specials: Mapping[str, r.SpecialRuleConfig | None] | None = None,
    records: Mapping[str, dict[str, r.RuleRecord]] | None = None,
) -> reg.Registry:
    """Build a Registry over invented ids, shaped like the committed ones.

    `specials` maps a Special id to the rule it stands for; `None` takes a rule
    permitting every Slot, named after the id — which is the whole point, since
    a test declaring `{"countdown": None}` may then write Instances of
    `countdown` anywhere in a Race. `records` adds or replaces a whole
    namespace, for the Sizes and Speeds a Unit names.
    """
    declared = {"fear": None} if specials is None else specials
    return reg.Registry(
        namespaces=_NAMESPACES,
        records={
            reg.SPECIAL: {
                identifier: rule
                if rule is not None
                else synthetic_special(name=identifier.replace("_", " ").title())
                for identifier, rule in declared.items()
            },
            "size": {"small": _modifier("Small", to_be_hit="-1")},
            "speed": {
                "slow": _modifier("Slow", to_be_hit="-1"),
                "fast": _modifier("Fast", to_be_hit="+1"),
            },
            "ability": {"good_shot": _modifier("Good Shot", to_hit="+1")},
            "terrain": {
                "forest": r.TerrainRuleConfig(name="Forest", effect="Blocks sight.")
            },
            "damage_type": {
                "poison": r.DamageTypeRuleConfig(name="Poison", effect="Poison damage.")
            },
            **(records or {}),
        },
    )


def _modifier(name: str, **fields: object) -> r.ModifierRuleConfig:
    """Build a record whose meaning is its to-hit numbers."""
    return r.ModifierRuleConfig.model_validate({"name": name} | fields)


_NAMESPACES = {
    name: r.NamespaceConfig(
        name=name.title(), label=name, file=f"{name}.toml", table=name
    )
    for name in ("special", "size", "speed", "ability", "terrain", "damage_type")
}
"""Where a synthetic Registry says its namespaces live. The files are never
read — a namespace is an abstract name, not a path (ADR 0024)."""


type InstallRegistry = Callable[..., reg.Registry]
"""The `install_registry` fixture: an optional Registry in, the installed one out."""


@pytest.fixture
def install_registry(monkeypatch: pytest.MonkeyPatch) -> InstallRegistry:
    """Answer every registry lookup from a synthetic Registry, for one test.

    Call it with the Registry to install, or with nothing for the default one.
    """

    def install(registry: reg.Registry | None = None) -> reg.Registry:
        installed = registry if registry is not None else synthetic_registry()
        for module in _registry_readers():
            monkeypatch.setattr(module, "load_registry", lambda *_, **__: installed)
        return installed

    return install


def _registry_readers() -> list[ModuleType]:
    """Every imported module that has to be told about an installed Registry.

    A module importing `load_registry` by name bound the function at import
    time, so patching `spf.registry` alone would leave it reading `rules/`.
    """
    return [
        reg,
        *(
            module
            for name, module in list(sys.modules.items())
            if name.startswith("spf.")
            and module is not None
            and getattr(module, "load_registry", None) is reg.load_registry
        ),
    ]
