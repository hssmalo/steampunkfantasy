"""ArmyUnit data structure and unit-level builder and cost functions."""

from dataclasses import dataclass, field

from spf.armies.model import ArmyModel
from spf.schemas import type_aliases as t
from spf.schemas.race import RaceConfig, UnitConfig


@dataclass(frozen=True)
class ArmyUnit:
    """One unit instance within a army, with its (possibly upgraded) model slots."""

    name: str
    config: UnitConfig = field(repr=False)
    models: tuple[ArmyModel, ...]


def _make_default_team_model(
    model_name: t.ModelName, race_config: RaceConfig
) -> ArmyModel:
    return ArmyModel(
        name=model_name, config=race_config.models[model_name], upgrades=()
    )


def _make_default_team_unit(unit_name: t.UnitName, race_config: RaceConfig) -> ArmyUnit:
    unit_config = race_config.units[unit_name]
    models = tuple(
        _make_default_team_model(model_name, race_config)
        for model_name in unit_config.models
    )
    return ArmyUnit(name=unit_name, config=unit_config, models=models)


def _resolve_model(
    unit: ArmyUnit, model_key: tuple[t.ModelName, int]
) -> tuple[int, ArmyModel]:
    """Return (index_in_tuple, ArmyModel) for the given (name, occurrence_index) key."""
    name, occurrence = model_key
    count = 0
    for i, model in enumerate(unit.models):
        if model.name == name:
            if count == occurrence:
                return i, model
            count += 1
    msg = f"Model '{model_key}' not found in unit '{unit.name}'"
    raise KeyError(msg)


def unit_cost(unit: ArmyUnit, race_config: RaceConfig) -> t.Cost:
    """Return the total cost for a single unit.

    Unit base cost + upgrade model costs + upgrade equipment costs.
    Equipment with upgrade_all=True is charged once; otherwise it's charged per model.
    """
    cost = t.Cost() + (unit.config.cost or t.Cost())
    num_models = len(unit.models)
    for i, team_model in enumerate(unit.models):
        # A model is an upgrade when its name differs from the default.
        if team_model.name != unit.config.models[i] and team_model.config.cost:
            cost = cost + team_model.config.cost
        for equip_key in team_model.upgrades:
            equip = race_config.equipment[equip_key]
            if equip.cost is None:
                continue
            # upgrade_all=False: per-model pricing — multiply by unit size.
            # upgrade_all=True or None: flat cost (None preserves legacy behavior).
            if equip.upgrade_all is False:
                cost = cost + equip.cost * num_models
            else:
                cost = cost + equip.cost
    return cost
