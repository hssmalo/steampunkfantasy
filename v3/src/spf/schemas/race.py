"""Schema for SteamPunkFantasy armies."""

from typing import Self

from pydantic import Field, model_validator

from spf.schemas import StrictModel
from spf.schemas import type_aliases as t


class RaceMetadata(StrictModel):
    name: str
    description: str = ""


class OrdersConfig(StrictModel):
    fire: dict[t.Speed, list[t.FireOrder]] | None = None
    movement: dict[t.Speed, list[t.MovementOrder]] | None = None


class UnitConfig(StrictModel):
    race: t.RaceName
    name: t.UnitName
    description: str = ""
    models: list[str]
    size: t.Size
    cost: t.Cost | None = None
    shaken: str
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
    special: list[str] = Field(default_factory=list)


class ModelConfig(StrictModel):
    race: t.RaceName
    name: t.ModelName
    description: str = ""
    equipment_limit: list[t.ParsedEquipmentLimit]
    equipments: list[str]
    type: list[t.ModelType]
    assault: AssaultConfig
    cost: t.Cost | None = None
    replaces: t.ModelName | None = None
    unit_special: dict[t.UnitSpecial, str] = Field(default_factory=dict)
    special: list[str] = Field(default_factory=list)


class Stacker[T](StrictModel):
    add: T | None = None
    replace: T | None = None
    append: T | None = None


class EquipmentAssaultConfig(StrictModel):
    strength: Stacker[t.Angles[int]] | None = None
    strength_die: Stacker[t.DieResult] | None = None
    deflection: Stacker[t.Angles[int]] | None = None
    deflection_die: Stacker[t.DieResult] | None = None
    damage: Stacker[t.Die] | None = None
    ap: Stacker[t.ArmorPenetration] | None = None
    special: Stacker[list[str]] | None = None


class EquipmentRangeConfig(StrictModel):
    range: int
    angle: t.Angles[bool | str]
    damage: t.Die
    ap: t.ArmorPenetration
    special: list[str] = Field(default_factory=list)


class EquipmentConfig(StrictModel):
    race: t.RaceName
    name: t.EquipmentName
    description: str = ""
    cost: t.Cost | None = None
    model_cost: t.Cost | None = None
    requires: list[list[t.ParsedRequirement]] = Field(default_factory=list)
    assault: EquipmentAssaultConfig | None = None
    range: EquipmentRangeConfig | None = None
    unit_special: dict[t.UnitSpecial, str] = Field(default_factory=dict)
    special: list[str] = Field(default_factory=list)
    orders_gained: OrdersConfig | None = None


class RaceConfig(StrictModel):
    races: dict[t.RaceName, RaceMetadata]
    units: dict[str, UnitConfig]
    models: dict[str, ModelConfig]
    equipments: dict[str, EquipmentConfig]

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
    def check_model_equipments(self) -> Self:
        """Check names of equipment listed under models."""
        equipment_names = self.equipments.keys()
        for model in self.models.values():
            if any(
                (failed := equipment) not in equipment_names
                for equipment in model.equipments
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
