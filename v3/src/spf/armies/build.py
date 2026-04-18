"""Build-time army data structures for assembling and mutating army lists.

These classes (ArmyList, ArmyUnit, ArmyModel) are the mutable assembly layer.
They carry config references for validation but are not self-contained.
Call ArmyList.resolve(race_config) to obtain a fully resolved Army.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

from spf.schemas import type_aliases as t
from spf.schemas.race import EquipmentConfig, ModelConfig, RaceConfig, UnitConfig

if TYPE_CHECKING:
    from spf.armies import Army


@dataclass(frozen=True)
class ArmyModel:
    """One model slot within an army unit, with any equipment upgrade keys applied."""

    name: str
    config: ModelConfig = field(repr=False)
    upgrades: tuple[str, ...]

    def upgrade(self, equipment_name: str, race_config: RaceConfig) -> Self:
        """Return a new ArmyModel with the given equipment upgrade added.

        Raises ValueError if the equipment has no cost or its requires are not
        satisfied.

        """
        equip = race_config.equipment[equipment_name]
        if equip.cost is None:
            msg = (
                f"Equipment '{equipment_name}' has no cost"
                " and cannot be used as an upgrade"
            )
            raise ValueError(msg)
        failed = _unsatisfied_groups(equip.requires, self, race_config)
        if failed:
            remaining = _remaining_slots(self, race_config)
            detail = "; ".join(_format_failed_group(g, remaining) for g in failed)
            msg = (
                f"Equipment '{equipment_name}' requires not satisfied"
                f" by model '{self.name}': {detail}"
            )
            raise ValueError(msg)
        return self.__class__(
            name=self.name,
            config=self.config,
            upgrades=(*self.upgrades, equipment_name),
        )


@dataclass(frozen=True)
class ArmyUnit:
    """One unit instance within an army list, with its model slots."""

    name: str
    config: UnitConfig = field(repr=False)
    models: tuple[ArmyModel, ...]

    def upgrade_model(
        self,
        model_key: tuple[t.ModelName, int],
        equipment_name: str,
        race_config: RaceConfig,
    ) -> Self:
        """Return a new ArmyUnit with an equipment upgrade applied to one model."""
        model_idx, model = _resolve_model(self, model_key)
        new_model = model.upgrade(equipment_name, race_config)
        new_models = (
            *self.models[:model_idx],
            new_model,
            *self.models[model_idx + 1 :],
        )
        return self.__class__(name=self.name, config=self.config, models=new_models)

    def upgrade_unit(
        self,
        model_key: tuple[t.ModelName, int],
        upgrade_model_name: str,
        race_config: RaceConfig,
    ) -> Self:
        """Return a new ArmyUnit with the identified model replaced by an upgrade model.

        The upgrade model's replaces field must equal the name of the model being
        replaced.

        """
        model_idx, existing = _resolve_model(self, model_key)
        upgrade_config = race_config.models[upgrade_model_name]
        if upgrade_config.replaces is None or existing.name != upgrade_config.replaces:
            msg = (
                f"Model '{upgrade_model_name}' cannot replace '{existing.name}': "
                f"not listed in its replaces field"
            )
            raise ValueError(msg)
        new_model = ArmyModel(
            name=upgrade_model_name, config=upgrade_config, upgrades=()
        )
        new_models = (
            *self.models[:model_idx],
            new_model,
            *self.models[model_idx + 1 :],
        )
        return self.__class__(name=self.name, config=self.config, models=new_models)


@dataclass(frozen=True)
class ArmyList:
    """A player's assembled force during construction, belonging to a single race."""

    race: t.RaceName
    nick: str
    units: tuple[ArmyUnit, ...]

    def add_unit(self, unit_name: t.UnitName, race_config: RaceConfig) -> Self:
        """Return a new ArmyList with the given unit appended at its default state."""
        if unit_name not in race_config.units:
            msg = f"Unknown unit '{unit_name}'"
            raise ValueError(msg)
        new_unit = _make_default_army_unit(unit_name, race_config)
        return self.__class__(
            race=self.race, nick=self.nick, units=(*self.units, new_unit)
        )

    def upgrade_unit(
        self,
        unit_key: tuple[t.UnitName, int],
        model_key: tuple[t.ModelName, int],
        upgrade_model_name: t.ModelName,
        race_config: RaceConfig,
    ) -> Self:
        """Return a new ArmyList with one model slot replaced by an upgrade model."""
        unit_idx, unit = _resolve_unit(self, unit_key)
        new_unit = unit.upgrade_unit(model_key, upgrade_model_name, race_config)
        new_units = (*self.units[:unit_idx], new_unit, *self.units[unit_idx + 1 :])
        return self.__class__(race=self.race, nick=self.nick, units=new_units)

    def upgrade_model(
        self,
        unit_key: tuple[t.UnitName, int],
        model_key: tuple[t.ModelName, int],
        equipment_name: t.EquipmentName,
        race_config: RaceConfig,
    ) -> Self:
        """Return a new ArmyList with one equipment upgrade added to a model slot."""
        unit_idx, unit = _resolve_unit(self, unit_key)
        new_unit = unit.upgrade_model(model_key, equipment_name, race_config)
        new_units = (*self.units[:unit_idx], new_unit, *self.units[unit_idx + 1 :])
        return self.__class__(race=self.race, nick=self.nick, units=new_units)

    def resolve(self, race_config: RaceConfig) -> "Army":
        """Return a fully resolved Army with all equipment configs populated.

        After resolve(), no race_config is needed for any computation on the
        result. Imports of Army, Model, Unit are done locally to avoid a
        circular import.
        """
        from spf.armies.army import Army  # noqa: PLC0415
        from spf.armies.model import Model  # noqa: PLC0415
        from spf.armies.unit import Unit  # noqa: PLC0415

        units = tuple(
            Unit(
                name=army_unit.name,
                config=army_unit.config,
                models=tuple(
                    Model(
                        name=army_model.name,
                        config=army_model.config,
                        default_equipment=tuple(
                            race_config.equipment[eq]
                            for eq in army_model.config.equipment
                        ),
                        upgrade_equipment=tuple(
                            race_config.equipment[eq] for eq in army_model.upgrades
                        ),
                    )
                    for army_model in army_unit.models
                ),
            )
            for army_unit in self.units
        )
        return Army(race=self.race, nick=self.nick, units=units)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_unit(
    army: ArmyList, unit_key: tuple[t.UnitName, int]
) -> tuple[int, ArmyUnit]:
    """Return (index, ArmyUnit) for the given (name, occurrence_index) key."""
    name, occurrence = unit_key
    count = 0
    for i, unit in enumerate(army.units):
        if unit.name == name:
            if count == occurrence:
                return i, unit
            count += 1
    msg = f"Unit '{unit_key}' not found in army"
    raise KeyError(msg)


def _resolve_model(
    unit: ArmyUnit, model_key: tuple[t.ModelName, int]
) -> tuple[int, ArmyModel]:
    """Return (index, ArmyModel) for the given (name, occurrence_index) key."""
    name, occurrence = model_key
    count = 0
    for i, model in enumerate(unit.models):
        if model.name == name:
            if count == occurrence:
                return i, model
            count += 1
    msg = f"Model '{model_key}' not found in unit '{unit.name}'"
    raise KeyError(msg)


def _make_default_army_model(
    model_name: t.ModelName, race_config: RaceConfig
) -> ArmyModel:
    return ArmyModel(
        name=model_name,
        config=race_config.models[model_name],
        upgrades=(),
    )


def _make_default_army_unit(unit_name: t.UnitName, race_config: RaceConfig) -> ArmyUnit:
    unit_config = race_config.units[unit_name]
    models = tuple(
        _make_default_army_model(model_name, race_config)
        for model_name in unit_config.models
    )
    return ArmyUnit(name=unit_name, config=unit_config, models=models)


def _remaining_slots(
    model: ArmyModel, race_config: RaceConfig
) -> dict[t.EquipmentHolder, int]:
    """Compute remaining holder slots after accounting for all upgrade equipment.

    Default equipment is never counted: when upgrades are present, defaults are
    discarded entirely. This also applies when checking whether the first upgrade
    can be added — adding any upgrade replaces the defaults, so they do not
    occupy slots for that check either.

    Slot usage is read from each equipment's requires field. In practice, holder
    requirements always appear in single-item OR-groups, so iterating all items
    in all groups gives the correct usage.
    """
    slots: dict[t.EquipmentHolder, int] = {
        limit.holder: limit.limit for limit in model.config.equipment_limit
    }
    # Defaults are discarded whenever upgrades are added, so only upgrades consume
    # slots. This holds even for the first upgrade: adding it replaces all defaults.
    for equip_key in model.upgrades:
        for req_group in race_config.equipment[equip_key].requires:
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
    available = remaining_slots.get(req.key, 0)  # type: ignore[arg-type]
    return isinstance(req.value, int) and available >= req.value


def _unsatisfied_groups(
    requires: list[list[t.Requirement]],
    model: ArmyModel,
    race_config: RaceConfig,
) -> list[list[t.Requirement]]:
    """Return OR-groups from requires that are not satisfied by model.

    An empty list means the model satisfies all requirement groups.
    """
    remaining = _remaining_slots(model, race_config)
    return [
        group
        for group in requires
        if not any(_satisfies_requirement(req, model, remaining) for req in group)
    ]


def _satisfies_requires(
    requires: list[list[t.Requirement]],
    model: ArmyModel,
    race_config: RaceConfig,
) -> bool:
    """Evaluate CNF requires: every outer group must have ≥1 satisfied inner req."""
    return not _unsatisfied_groups(requires, model, race_config)


def _format_failed_group(
    group: list[t.Requirement],
    remaining_slots: dict[t.EquipmentHolder, int],
) -> str:
    """Format a failing OR-group as a human-readable constraint description."""
    parts: list[str] = []
    for req in group:
        if req.key == "type":
            parts.append(f"type:{req.value}")
        else:
            available = remaining_slots.get(req.key, 0)  # type: ignore[arg-type]
            parts.append(f"{req.key}:{req.value} (have {available})")
    return "needs " + " or ".join(parts)


def available_models(
    army: ArmyList,
    unit_key: tuple[t.UnitName, int],
    model_key: tuple[t.ModelName, int],
    race_config: RaceConfig,
) -> list[ModelConfig]:
    """Return army models whose replaces field equals the given model's name."""
    _, unit = _resolve_unit(army, unit_key)
    _, model = _resolve_model(unit, model_key)
    return [
        cfg
        for cfg in race_config.models.values()
        if cfg.replaces is not None and model.name == cfg.replaces
    ]


def available_equipment(
    army: ArmyList,
    unit_key: tuple[t.UnitName, int],
    model_key: tuple[t.ModelName, int],
    race_config: RaceConfig,
) -> list[EquipmentConfig]:
    """Return equipment upgrades valid for the given model.

    Valid means: has a cost and satisfies the model's requires constraints.
    """
    _, unit = _resolve_unit(army, unit_key)
    _, model = _resolve_model(unit, model_key)
    return [
        cfg
        for cfg in race_config.equipment.values()
        if cfg.cost is not None
        and _satisfies_requires(cfg.requires, model, race_config)
    ]


def validate_army(army: ArmyList, race_config: RaceConfig) -> list[str]:
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
            # Validate equipment upgrades sequentially: check each upgrade against
            # a partial model containing only the *prior* upgrades. This mirrors the
            # build-time upgrade() semantics and prevents an upgrade from being counted
            # against its own slot requirement.
            for j, equip_key in enumerate(team_model.upgrades):
                equip = race_config.equipment[equip_key]
                if equip.cost is None:
                    errors.append(
                        f"Unit '{unit.name}', model '{team_model.name}': "
                        f"equipment '{equip_key}' has no cost"
                        " and cannot be used as upgrade"
                    )
                else:
                    partial_model = ArmyModel(
                        name=team_model.name,
                        config=team_model.config,
                        upgrades=team_model.upgrades[:j],
                    )
                    failed = _unsatisfied_groups(
                        equip.requires, partial_model, race_config
                    )
                    if failed:
                        remaining = _remaining_slots(partial_model, race_config)
                        detail = "; ".join(
                            _format_failed_group(g, remaining) for g in failed
                        )
                        errors.append(
                            f"Unit '{unit.name}', model '{team_model.name}': "
                            f"equipment '{equip_key}' requires not satisfied: {detail}"
                        )
    return errors
