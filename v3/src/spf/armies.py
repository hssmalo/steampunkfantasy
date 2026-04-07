"""Army data structures and builder functions for SteamPunkFantasy."""

from dataclasses import dataclass, field

from spf.schemas import type_aliases as t
from spf.schemas.race import EquipmentConfig, ModelConfig, RaceConfig, UnitConfig


@dataclass(frozen=True)
class ArmyModel:
    """One model slot within a team unit, with any equipment upgrades applied."""

    name: str
    config: ModelConfig = field(repr=False)
    # Equipment keys added by the player as upgrades; excludes config.equipments defaults.
    upgrades: tuple[str, ...]


@dataclass(frozen=True)
class ArmyUnit:
    """One unit instance within a team, with its (possibly upgraded) model slots."""

    name: str
    config: UnitConfig = field(repr=False)
    # Positionally matches config.models; entries may be upgrade replacements.
    models: tuple[ArmyModel, ...]


@dataclass(frozen=True)
class Army:
    """A player's assembled force from a single army."""

    race: t.RaceName
    units: tuple[ArmyUnit, ...]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


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


def _add_cost(a: t.Cost, b: t.Cost | None) -> t.Cost:
    if b is None:
        return a
    return t.Cost(mp=a.mp + b.mp, cp=a.cp + b.cp, xp=a.xp + b.xp, ip=a.ip + b.ip)


def _remaining_slots(
    model: ArmyModel, race_config: RaceConfig
) -> dict[t.EquipmentHolder, int]:
    """Compute remaining holder slots after all current equipment (defaults + upgrades).

    Slot usage is read from each equipment's requires field. In practice, holder
    requirements always appear in single-item OR-groups, so iterating all items
    in all groups gives the correct usage. If an OR-group contained multiple holder
    requirements in the future, this would over-count; revisit then.
    """
    slots: dict[t.EquipmentHolder, int] = {
        limit.holder: limit.limit for limit in model.config.equipment_limit
    }
    for equip_key in (*model.config.equipments, *model.upgrades):
        for req_group in race_config.equipments[equip_key].requires:
            for req in req_group:
                if (
                    req.key != "type"
                    and isinstance(req.value, int)
                    and req.key in slots
                ):
                    slots[req.key] -= req.value  # type: ignore[index]
    return slots


def _satisfies_requirement(
    req: t.Requirement,
    model: ArmyModel,
    remaining_slots: dict[t.EquipmentHolder, int],
) -> bool:
    if req.key == "type":
        return req.value in model.config.type
    available = remaining_slots.get(req.key, 0)
    return isinstance(req.value, int) and available >= req.value


def _satisfies_requires(
    requires: list[list[t.Requirement]],
    model: ArmyModel,
    race_config: RaceConfig,
) -> bool:
    """Evaluate CNF requires: every outer group must have ≥1 satisfied inner requirement."""
    remaining = _remaining_slots(model, race_config)
    return all(
        any(_satisfies_requirement(req, model, remaining) for req in group)
        for group in requires
    )


def _resolve_unit(team: Army, unit_key: tuple[t.UnitName, int]) -> tuple[int, ArmyUnit]:
    """Return (position_in_tuple, ArmyUnit) for the given (name, occurrence_index) key."""
    name, occurrence = unit_key
    count = 0
    for i, unit in enumerate(team.units):
        if unit.name == name:
            if count == occurrence:
                return i, unit
            count += 1
    raise KeyError(f"Unit {unit_key!r} not found in team")


def _resolve_model(
    unit: ArmyUnit, model_key: tuple[t.ModelName, int]
) -> tuple[int, ArmyModel]:
    """Return (position_in_tuple, ArmyModel) for the given (name, occurrence_index) key."""
    name, occurrence = model_key
    count = 0
    for i, model in enumerate(unit.models):
        if model.name == name:
            if count == occurrence:
                return i, model
            count += 1
    raise KeyError(f"Model {model_key!r} not found in unit {unit.name!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def add_unit(team: Army, unit_name: t.UnitName, race_config: RaceConfig) -> Army:
    """Return a new Army with a unit (and its default models) appended."""
    if unit_name not in race_config.units:
        raise ValueError(f"Unknown unit {unit_name!r}")
    new_unit = _make_default_team_unit(unit_name, race_config)
    return Army(race=team.race, units=(*team.units, new_unit))


def upgrade_unit(
    team: Army,
    unit_key: tuple[t.UnitName, int],
    model_key: tuple[t.ModelName, int],
    upgrade_model_name: t.ModelName,
    race_config: RaceConfig,
) -> Army:
    """Return a new Army with one model slot replaced by an upgrade model.

    The upgrade model's replaces list must include the name of the model being replaced.
    """
    unit_idx, unit = _resolve_unit(team, unit_key)
    model_idx, existing = _resolve_model(unit, model_key)

    upgrade_config = race_config.models[upgrade_model_name]
    if upgrade_config.replaces is None or existing.name not in upgrade_config.replaces:
        raise ValueError(
            f"Model {upgrade_model_name!r} cannot replace {existing.name!r}: "
            f"not listed in its replaces field"
        )

    new_model = ArmyModel(name=upgrade_model_name, config=upgrade_config, upgrades=())
    new_models = (*unit.models[:model_idx], new_model, *unit.models[model_idx + 1 :])
    new_unit = ArmyUnit(name=unit.name, config=unit.config, models=new_models)
    new_units = (*team.units[:unit_idx], new_unit, *team.units[unit_idx + 1 :])
    return Army(race=team.race, units=new_units)


def upgrade_model(
    team: Army,
    unit_key: tuple[t.UnitName, int],
    model_key: tuple[t.ModelName, int],
    equipment_name: t.EquipmentName,
    race_config: RaceConfig,
) -> Army:
    """Return a new Army with one equipment upgrade added to a model slot."""
    unit_idx, unit = _resolve_unit(team, unit_key)
    model_idx, model = _resolve_model(unit, model_key)

    equip = race_config.equipments[equipment_name]
    if equip.cost is None:
        raise ValueError(
            f"Equipment {equipment_name!r} has no cost and cannot be used as an upgrade"
        )
    if not _satisfies_requires(equip.requires, model, race_config):
        raise ValueError(
            f"Equipment {equipment_name!r} requires are not satisfied by model {model.name!r}"
        )

    new_model = ArmyModel(
        name=model.name, config=model.config, upgrades=(*model.upgrades, equipment_name)
    )
    new_models = (*unit.models[:model_idx], new_model, *unit.models[model_idx + 1 :])
    new_unit = ArmyUnit(name=unit.name, config=unit.config, models=new_models)
    new_units = (*team.units[:unit_idx], new_unit, *team.units[unit_idx + 1 :])
    return Army(race=team.race, units=new_units)


def available_models(
    team: Army,
    unit_key: tuple[t.UnitName, int],
    model_key: tuple[t.ModelName, int],
    race_config: RaceConfig,
) -> list[ModelConfig]:
    """Return army models whose replaces list includes the given model's name."""
    _, unit = _resolve_unit(team, unit_key)
    _, model = _resolve_model(unit, model_key)
    return [
        cfg
        for cfg in race_config.models.values()
        if cfg.replaces is not None and model.name in cfg.replaces
    ]


def available_equipment(
    team: Army,
    unit_key: tuple[t.UnitName, int],
    model_key: tuple[t.ModelName, int],
    race_config: RaceConfig,
) -> list[EquipmentConfig]:
    """Return equipment upgrades valid for the given model (have cost, satisfies requires)."""
    _, unit = _resolve_unit(team, unit_key)
    _, model = _resolve_model(unit, model_key)
    return [
        cfg
        for cfg in race_config.equipments.values()
        if cfg.cost is not None
        and _satisfies_requires(cfg.requires, model, race_config)
    ]


def total_cost(team: Army, race_config: RaceConfig) -> t.Cost:
    """Return the total cost: unit base costs + upgrade model costs + upgrade equipment costs."""
    cost = t.Cost()
    for unit in team.units:
        cost = _add_cost(cost, unit.config.cost)
        for i, team_model in enumerate(unit.models):
            # A model is an upgrade when its name differs from the unit's default at this position.
            if team_model.name != unit.config.models[i]:
                cost = _add_cost(cost, team_model.config.cost)
            for equip_key in team_model.upgrades:
                cost = _add_cost(cost, race_config.equipments[equip_key].cost)
    return cost


def validate_team(team: Army, race_config: RaceConfig) -> list[str]:
    """Return all rule violations in the team. Empty list means the team is valid."""
    errors: list[str] = []
    for unit in team.units:
        for i, team_model in enumerate(unit.models):
            default_model_name = unit.config.models[i]
            # Validate model replacement
            if team_model.name != default_model_name:
                replaces = team_model.config.replaces or []
                if default_model_name not in replaces:
                    errors.append(
                        f"Unit {unit.name!r}: model {team_model.name!r} cannot replace "
                        f"{default_model_name!r} (not in its replaces list)"
                    )
            # Validate equipment upgrades
            for equip_key in team_model.upgrades:
                equip = race_config.equipments[equip_key]
                if equip.cost is None:
                    errors.append(
                        f"Unit {unit.name!r}, model {team_model.name!r}: "
                        f"equipment {equip_key!r} has no cost and cannot be used as upgrade"
                    )
                elif not _satisfies_requires(equip.requires, team_model, race_config):
                    errors.append(
                        f"Unit {unit.name!r}, model {team_model.name!r}: "
                        f"equipment {equip_key!r} requires are not satisfied"
                    )
    return errors
