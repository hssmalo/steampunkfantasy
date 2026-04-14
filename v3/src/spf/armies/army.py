"""Army data structure and army-level builder, query, and validation functions."""

from dataclasses import dataclass

from spf.armies.model import (
    ArmyModel,
    _format_failed_group,
    _remaining_slots,
    _satisfies_requires,
    _unsatisfied_groups,
)
from spf.armies.unit import (
    ArmyUnit,
    _make_default_team_unit,
    _resolve_model,
    unit_cost,
)
from spf.schemas import type_aliases as t
from spf.schemas.race import EquipmentConfig, ModelConfig, RaceConfig


@dataclass(frozen=True)
class Army:
    """A player's assembled force from a single army."""

    race: t.RaceName
    nick: str
    units: tuple[ArmyUnit, ...]


def _resolve_unit(army: Army, unit_key: tuple[t.UnitName, int]) -> tuple[int, ArmyUnit]:
    """Return (index_in_tuple, ArmyUnit) for the given (name, occurrence_index) key."""
    name, occurrence = unit_key
    count = 0
    for i, unit in enumerate(army.units):
        if unit.name == name:
            if count == occurrence:
                return i, unit
            count += 1
    msg = f"Unit '{unit_key}' not found in army"
    raise KeyError(msg)


def add_unit(army: Army, unit_name: t.UnitName, race_config: RaceConfig) -> Army:
    """Return a new Army with a unit (and its default models) appended."""
    if unit_name not in race_config.units:
        msg = f"Unknown unit '{unit_name}'"
        raise ValueError(msg)
    new_unit = _make_default_team_unit(unit_name, race_config)
    return Army(race=army.race, nick=army.nick, units=(*army.units, new_unit))


def upgrade_unit(
    army: Army,
    unit_key: tuple[t.UnitName, int],
    model_key: tuple[t.ModelName, int],
    upgrade_model_name: t.ModelName,
    race_config: RaceConfig,
) -> Army:
    """Return a new Army with one model slot replaced by an upgrade model.

    The upgrade model's replaces list must include the name of the model being replaced.
    """
    unit_idx, unit = _resolve_unit(army, unit_key)
    model_idx, existing = _resolve_model(unit, model_key)

    upgrade_config = race_config.models[upgrade_model_name]
    if upgrade_config.replaces is None or existing.name != upgrade_config.replaces:
        msg = (
            f"Model '{upgrade_model_name}' cannot replace '{existing.name}': "
            f"not listed in its replaces field"
        )
        raise ValueError(msg)

    new_model = ArmyModel(name=upgrade_model_name, config=upgrade_config, upgrades=())
    new_models = (*unit.models[:model_idx], new_model, *unit.models[model_idx + 1 :])
    new_unit = ArmyUnit(name=unit.name, config=unit.config, models=new_models)
    new_units = (*army.units[:unit_idx], new_unit, *army.units[unit_idx + 1 :])
    return Army(race=army.race, nick=army.nick, units=new_units)


def upgrade_model(
    army: Army,
    unit_key: tuple[t.UnitName, int],
    model_key: tuple[t.ModelName, int],
    equipment_name: t.EquipmentName,
    race_config: RaceConfig,
) -> Army:
    """Return a new Army with one equipment upgrade added to a model slot."""
    unit_idx, unit = _resolve_unit(army, unit_key)
    model_idx, model = _resolve_model(unit, model_key)

    equip = race_config.equipment[equipment_name]
    if equip.cost is None:
        msg = (
            f"Equipment '{equipment_name}' has no cost and cannot be used as an upgrade"
        )
        raise ValueError(msg)
    failed = _unsatisfied_groups(equip.requires, model, race_config)
    if failed:
        remaining = _remaining_slots(model, race_config)
        detail = "; ".join(_format_failed_group(g, remaining) for g in failed)
        msg = (
            f"Equipment '{equipment_name}' requires not satisfied"
            f" by model '{model.name}': {detail}"
        )
        raise ValueError(msg)

    new_model = ArmyModel(
        name=model.name, config=model.config, upgrades=(*model.upgrades, equipment_name)
    )
    new_models = (*unit.models[:model_idx], new_model, *unit.models[model_idx + 1 :])
    new_unit = ArmyUnit(name=unit.name, config=unit.config, models=new_models)
    new_units = (*army.units[:unit_idx], new_unit, *army.units[unit_idx + 1 :])
    return Army(race=army.race, nick=army.nick, units=new_units)


def available_models(
    army: Army,
    unit_key: tuple[t.UnitName, int],
    model_key: tuple[t.ModelName, int],
    race_config: RaceConfig,
) -> list[ModelConfig]:
    """Return army models whose replaces list includes the given model's name."""
    _, unit = _resolve_unit(army, unit_key)
    _, model = _resolve_model(unit, model_key)
    return [
        cfg
        for cfg in race_config.models.values()
        if cfg.replaces is not None and model.name == cfg.replaces
    ]


def available_equipment(
    army: Army,
    unit_key: tuple[t.UnitName, int],
    model_key: tuple[t.ModelName, int],
    race_config: RaceConfig,
) -> list[EquipmentConfig]:
    """Return equipment upgrades valid for the given model.

    The upgrade has a cost and satisfies requires.
    """
    _, unit = _resolve_unit(army, unit_key)
    _, model = _resolve_model(unit, model_key)
    return [
        cfg
        for cfg in race_config.equipment.values()
        if cfg.cost is not None
        and _satisfies_requires(cfg.requires, model, race_config)
    ]


def total_cost(army: Army, race_config: RaceConfig) -> t.Cost:
    """Return the total cost.

    Unit base costs + upgrade model costs + upgrade equipment costs.
    """
    return sum((unit_cost(unit, race_config) for unit in army.units), t.Cost())


def validate_army(army: Army, race_config: RaceConfig) -> list[str]:
    """Return all rule violations in the army. Empty list means the army is valid."""
    errors: list[str] = []
    for unit in army.units:
        for i, team_model in enumerate(unit.models):
            default_model_name = unit.config.models[i]
            # Validate model replacement
            if default_model_name not in {team_model.name, team_model.config.replaces}:
                errors.append(
                    f"Unit '{unit.name}': model '{team_model.name}' cannot replace "
                    f"'{default_model_name}' (not in its replaces list)"
                )
            # Validate equipment upgrades
            for equip_key in team_model.upgrades:
                equip = race_config.equipment[equip_key]
                if equip.cost is None:
                    errors.append(
                        f"Unit '{unit.name}', model '{team_model.name}': "
                        f"equipment '{equip_key}' has no cost"
                        " and cannot be used as upgrade"
                    )
                else:
                    failed = _unsatisfied_groups(
                        equip.requires, team_model, race_config
                    )
                    if failed:
                        remaining = _remaining_slots(team_model, race_config)
                        detail = "; ".join(
                            _format_failed_group(g, remaining) for g in failed
                        )
                        errors.append(
                            f"Unit '{unit.name}', model '{team_model.name}': "
                            f"equipment '{equip_key}' requires not satisfied: {detail}"
                        )
    return errors
