"""Schema for SteamPunkFantasy armies."""

from typing import Any, Self

from pydantic import Field, model_validator

from spf.schemas import StrictModel
from spf.schemas import type_aliases as t


class RaceMetadata(StrictModel):
    name: str
    description: str = ""


class OrdersConfig(StrictModel):
    fire: dict[t.Speed, list[t.FireOrder]] | None = None
    movement: dict[t.Speed, list[t.MovementOrder]] | None = None


class ShakenConfig(StrictModel):
    speed: t.Speed
    movement_order: t.MovementOrder
    fire_order: str = "Can't use weapons"
    comment: str = ""


class UnitConfig(StrictModel):
    race: t.RaceName
    name: t.UnitName
    description: str = ""
    tip: str = ""
    lore: str = ""
    ai_guid: str = ""
    models: list[str]
    size: t.Size
    cost: t.Cost | None = None
    shaken: ShakenConfig
    special: dict[t.UnitSpecial, str] = Field(default_factory=dict)
    orders: OrdersConfig
    armor: t.Angles[int] | None = None
    damage_tables: dict[t.DamageTableName, t.DamageTable]


class AssaultConfig(StrictModel):
    strength: t.Angles[int]
    strength_die: t.DieResult
    deflection: t.Angles[int]
    deflection_die: t.DieResult
    damage: t.Die
    ap: t.ArmorPenetration
    special: dict[t.AssaultSpecial, str] = Field(default_factory=dict)


class ModelConfig(StrictModel):
    race: t.RaceName
    name: t.ModelName
    description: str = ""
    equipment_limit: list[t.ParsedEquipmentLimit]
    equipment: list[str]
    type: list[t.ModelType]
    assault: AssaultConfig
    cost: t.Cost | None = None
    replaces: t.ModelName | None = None
    unit_special: dict[t.UnitSpecial, str] = Field(default_factory=dict)
    special: dict[t.ModelSpecial, str] = Field(default_factory=dict)


class Stacker[T](StrictModel):
    add: T | None = None
    replace: T | None = None
    extend: T | None = None


class EquipmentAssaultConfig(StrictModel):
    strength: Stacker[t.Angles[int]] | None = None
    strength_die: Stacker[t.DieResult] | None = None
    deflection: Stacker[t.Angles[int]] | None = None
    deflection_die: Stacker[t.DieResult] | None = None
    damage: Stacker[t.Die] | None = None
    ap: Stacker[t.ArmorPenetration] | None = None
    special: dict[t.AssaultSpecial, str] = Field(default_factory=dict)


class EquipmentRangeConfig(StrictModel):
    range: int
    angle: t.Angles[bool | str]
    damage: t.Die
    ap: t.ArmorPenetration
    special: dict[t.RangeSpecial, str] = Field(default_factory=dict)


class EquipmentConfig(StrictModel):
    race: t.RaceName
    name: t.EquipmentName
    description: str = ""
    cost: t.Cost | None = None
    upgrade_all: bool | None = None
    requires: list[list[t.ParsedRequirement]] = Field(default_factory=list)
    assault: EquipmentAssaultConfig | None = None
    range: EquipmentRangeConfig | None = None
    unit_special: dict[t.UnitSpecial, str] = Field(default_factory=dict)
    model_special: dict[t.ModelSpecial, str] = Field(default_factory=dict)
    orders_gained: OrdersConfig | None = None

    @model_validator(mode="after")
    def check_upgrade_all_matches_cost(self) -> Self:
        """Require upgrade_all iff cost is set."""
        if (self.cost is None) != (self.upgrade_all is None):
            msg = (
                f"Equipment '{self.name}': 'upgrade_all' must be set"
                " if and only if 'cost' is set"
            )
            raise ValueError(msg)
        return self


class SpawnConfig(StrictModel):
    unit: t.UnitName
    equipment: list[t.EquipmentName] = Field(default_factory=list)
    copy_equipment: bool = False


def _validate_specials(
    spawns: set[str], special_dict: dict[Any, str], context: str
) -> None:
    for rule_name, rule_value in special_dict.items():
        if rule_name not in ("Spawn", "Not Yet Dead"):
            continue
        if ":" not in rule_value:
            msg = (
                f"Special rule '{rule_name}' in {context} must follow the format "
                f"'[spawn_id]: [placement_text]'. Got: '{rule_value}'"
            )
            raise ValueError(msg)
        spawn_id, _ = rule_value.split(":", 1)
        spawn_id = spawn_id.strip()
        if spawn_id not in spawns:
            msg = (
                f"Special rule '{rule_name}' in {context} references undefined "
                f"spawn ID '{spawn_id}'"
            )
            raise ValueError(msg)


class RaceConfig(StrictModel):
    races: dict[t.RaceName, RaceMetadata]
    units: dict[str, UnitConfig]
    models: dict[str, ModelConfig]
    equipment: dict[str, EquipmentConfig]
    spawns: dict[str, SpawnConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_spawns(self) -> Self:
        """Validate spawns catalog and references in special rules."""
        # 1. Validate that for every key in spawns, spawns[key].unit is in self.units
        for spawn_id, spawn in self.spawns.items():
            if spawn.unit not in self.units:
                msg = f"Spawn '{spawn_id}' references invalid unit '{spawn.unit}'"
                raise ValueError(msg)
            for eq in spawn.equipment:
                if eq not in self.equipment:
                    msg = f"Spawn '{spawn_id}' references invalid equipment '{eq}'"
                    raise ValueError(msg)

        spawns_keys = set(self.spawns.keys())

        # Check all units
        for unit in self.units.values():
            _validate_specials(spawns_keys, unit.special, f"unit '{unit.name}'")

        # Check all models
        for model in self.models.values():
            _validate_specials(
                spawns_keys,
                model.unit_special,
                f"model '{model.name}' unit_special",
            )
            _validate_specials(
                spawns_keys, model.special, f"model '{model.name}' special"
            )
            _validate_specials(
                spawns_keys,
                model.assault.special,
                f"model '{model.name}' assault special",
            )

        # Check all equipment
        for eq in self.equipment.values():
            _validate_specials(
                spawns_keys,
                eq.unit_special,
                f"equipment '{eq.name}' unit_special",
            )
            _validate_specials(
                spawns_keys,
                eq.model_special,
                f"equipment '{eq.name}' model_special",
            )
            if eq.assault is not None:
                _validate_specials(
                    spawns_keys,
                    eq.assault.special,
                    f"equipment '{eq.name}' assault special",
                )
            if eq.range is not None:
                _validate_specials(
                    spawns_keys,
                    eq.range.special,
                    f"equipment '{eq.name}' range special",
                )

        return self

    @model_validator(mode="after")
    def check_unit_models(self) -> Self:
        """Check names of models listed under units."""
        model_names = self.models.keys()
        for unit in self.units.values():
            if any((failed := model) not in model_names for model in unit.models):
                msg = f"'{failed}' not a valid model name for {unit.name}"
                raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def check_model_equipment(self) -> Self:
        """Check names of equipment listed under models."""
        equipment_names = self.equipment.keys()
        for model in self.models.values():
            if any(
                (failed := equipment) not in equipment_names
                for equipment in model.equipment
            ):
                msg = f"'{failed}' not a valid model name for {model.name}"
                raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def check_model_replaces(self) -> Self:
        """Check names of model upgrades is model name."""
        model_names = self.models.keys()
        for model in self.models.values():
            if model.replaces is not None and model.replaces not in model_names:
                msg = (
                    f"'{model.replaces}' is not a valid model"
                    f" name for {model.name} replacement"
                )
                raise ValueError(msg)
        return self
