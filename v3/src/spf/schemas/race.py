"""Schema for SteamPunkFantasy armies."""

from collections.abc import Iterator
from typing import Self

from pydantic import Field, model_validator

from spf import registry
from spf.schemas import StrictModel
from spf.schemas import type_aliases as t
from spf.schemas.special import SpecialInstance, Specials


class RaceMetadata(StrictModel):
    name: str
    description: str = ""


class OrdersConfig(StrictModel):
    fire: dict[str, list[t.FireOrder]] | None = None
    movement: dict[str, list[t.MovementOrder]] | None = None


class ShakenConfig(StrictModel):
    speed: str
    movement_order: t.MovementOrder
    fire_order: str = "Can't use weapons"
    comment: str = ""


class Stacker[T](StrictModel):
    add: T | None = None
    replace: T | None = None
    extend: T | None = None


class UnitStatModifierConfig(StrictModel):
    """Modifiers a Model or an Equipment applies to the stats of its Unit.

    The list of fields *is* the scope fence: `extra="forbid"` rejects a
    modifier of anything not named here, so widening it is a visible act
    rather than an open-ended effects engine (ADR 0024).

    `armor` gets the full `Stacker`. Every case in the data is additive —
    `[3, 2, 0, 0]` on a Unit whose base armor is `[8, 6, 5, 4]` is a grant, and
    overwriting would *drop* that Unit's front arc from 8 to 3.
    """

    armor: Stacker[t.Angles[int]] | None = None


class UnitConfig(StrictModel):
    race: t.RaceName
    name: t.UnitName
    description: str = ""
    tip: str = ""
    lore: str = ""
    ai_guid: str = ""
    models: list[str]
    size: str
    cost: t.Cost | None = None
    shaken: ShakenConfig
    specials: Specials = Field(default_factory=dict)
    note: str = ""
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
    specials: Specials = Field(default_factory=dict)
    note: str = ""


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
    unit_specials: Specials = Field(default_factory=dict)
    specials: Specials = Field(default_factory=dict)
    unit: UnitStatModifierConfig | None = None
    note: str = ""


class EquipmentAssaultConfig(StrictModel):
    strength: Stacker[t.Angles[int]] | None = None
    strength_die: Stacker[t.DieResult] | None = None
    deflection: Stacker[t.Angles[int]] | None = None
    deflection_die: Stacker[t.DieResult] | None = None
    damage: Stacker[t.Die] | None = None
    ap: Stacker[t.ArmorPenetration] | None = None
    specials: Specials = Field(default_factory=dict)
    note: str = ""


class EquipmentRangeConfig(StrictModel):
    range: int
    angle: t.Angles[bool | str]
    damage: t.Die
    ap: t.ArmorPenetration
    specials: Specials = Field(default_factory=dict)
    note: str = ""


class EquipmentConfig(StrictModel):
    race: t.RaceName
    name: t.EquipmentName
    description: str = ""
    cost: t.Cost | None = None
    upgrade_all: bool | None = None
    requires: list[list[t.ParsedRequirement]] = Field(default_factory=list)
    assault: EquipmentAssaultConfig | None = None
    range: EquipmentRangeConfig | None = None
    unit_specials: Specials = Field(default_factory=dict)
    model_specials: Specials = Field(default_factory=dict)
    unit: UnitStatModifierConfig | None = None
    note: str = ""
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


SPAWNING_SPECIALS = ("spawn", "not_yet_dead")
"""The Special ids whose prose names the spawn it places."""


def spawn_reference(instance: SpecialInstance) -> str | None:
    """Return the spawn a spawning instance places, or `None` when it names none.

    Which spawn a Spawn places is prose the rule has yet to formalize, so it is
    read off the front of the instance's own `text` — `'[spawn_id]: [placement
    text]'` — rather than out of an argument. One reader, so a Rendering that
    follows the reference and the validation that guards it cannot disagree
    about where the id ends.
    """
    text = instance.text or ""
    if ":" not in text:
        return None
    return text.split(":", 1)[0].strip()


def spawns_placed(specials: Specials) -> Iterator[str]:
    """Every spawn the spawning instances of one Slot name, in printed order."""
    for rule_name in SPAWNING_SPECIALS:
        for instance in specials.get(rule_name, []):
            if (spawn_id := spawn_reference(instance)) is not None:
                yield spawn_id


def _validate_specials(spawns: set[str], specials: Specials, *, context: str) -> None:
    """Check that every spawning instance names a spawn the catalogue holds."""
    for rule_name in SPAWNING_SPECIALS:
        for instance in specials.get(rule_name, []):
            spawn_id = spawn_reference(instance)
            if spawn_id is None:
                msg = (
                    f"Special rule '{rule_name}' in {context} must follow the format "
                    f"'[spawn_id]: [placement_text]'. Got: '{instance.text or ''}'"
                )
                raise ValueError(msg)
            if spawn_id not in spawns:
                msg = (
                    f"Special rule '{rule_name}' in {context} references undefined "
                    f"spawn ID '{spawn_id}'"
                )
                raise ValueError(msg)


def _order_speeds(orders: OrdersConfig | None) -> list[str]:
    """Every Speed an orders table is keyed by, fire rows then movement rows."""
    if orders is None:
        return []
    return [*(orders.fire or {}), *(orders.movement or {})]


def _check_ids(
    values: list[str], *, namespace: str, context: str, rules: registry.Registry
) -> list[str]:
    """Report every value that is not an identifier in the named registry."""
    known = rules.records.get(namespace, {})
    return [
        f"{context}: '{value}' is not a {namespace}"
        for value in values
        if value not in known
    ]


class RaceConfig(StrictModel):
    races: dict[t.RaceName, RaceMetadata]
    units: dict[str, UnitConfig]
    models: dict[str, ModelConfig]
    equipment: dict[str, EquipmentConfig]
    spawns: dict[str, SpawnConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_special_instances(self) -> Self:
        """Resolve every Special instance against the rule registries.

        The hard gate (ADR 0024). It runs here rather than per record because
        the message has to name the holder the instance sits on, and every
        error is collected so one load names them all.
        """
        rules = registry.load_registry()
        errors: list[str] = []
        for unit in self.units.values():
            errors += registry.check_instances(
                unit.specials,
                slot="unit",
                context=f"unit '{unit.name}'",
                registry=rules,
            )
        for model in self.models.values():
            where = f"model '{model.name}'"
            errors += registry.check_instances(
                model.unit_specials, slot="unit", context=where, registry=rules
            )
            errors += registry.check_instances(
                model.specials, slot="model", context=where, registry=rules
            )
            errors += registry.check_instances(
                model.assault.specials, slot="assault", context=where, registry=rules
            )
        for equip in self.equipment.values():
            where = f"equipment '{equip.name}'"
            errors += registry.check_instances(
                equip.unit_specials, slot="unit", context=where, registry=rules
            )
            errors += registry.check_instances(
                equip.model_specials, slot="model", context=where, registry=rules
            )
            if equip.assault is not None:
                errors += registry.check_instances(
                    equip.assault.specials,
                    slot="assault",
                    context=where,
                    registry=rules,
                )
            if equip.range is not None:
                errors += registry.check_instances(
                    equip.range.specials, slot="range", context=where, registry=rules
                )
        if errors:
            raise ValueError("\n".join(errors))
        return self

    @model_validator(mode="after")
    def check_vocabulary(self) -> Self:
        """Check every Speed and Size against the registry that owns it.

        A Unit's `size`, its `shaken.speed` and the keys of every orders table
        are identifiers in the `size` and `speed` registries (ADR 0024), so
        they are checked the same way a Special id is — against the registry,
        not against a list kept alongside it.
        """
        rules = registry.load_registry()
        errors: list[str] = []
        for unit in self.units.values():
            where = f"unit '{unit.name}'"
            errors += _check_ids(
                [unit.size], namespace="size", context=where, rules=rules
            )
            errors += _check_ids(
                [unit.shaken.speed, *_order_speeds(unit.orders)],
                namespace="speed",
                context=where,
                rules=rules,
            )
        for equip in self.equipment.values():
            errors += _check_ids(
                _order_speeds(equip.orders_gained),
                namespace="speed",
                context=f"equipment '{equip.name}'",
                rules=rules,
            )
        if errors:
            raise ValueError("\n".join(errors))
        return self

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
            _validate_specials(
                spawns_keys, unit.specials, context=f"unit '{unit.name}'"
            )

        # Check all models
        for model in self.models.values():
            _validate_specials(
                spawns_keys,
                model.unit_specials,
                context=f"model '{model.name}' unit specials",
            )
            _validate_specials(
                spawns_keys, model.specials, context=f"model '{model.name}' specials"
            )
            _validate_specials(
                spawns_keys,
                model.assault.specials,
                context=f"model '{model.name}' assault specials",
            )

        # Check all equipment
        for eq in self.equipment.values():
            _validate_specials(
                spawns_keys,
                eq.unit_specials,
                context=f"equipment '{eq.name}' unit specials",
            )
            _validate_specials(
                spawns_keys,
                eq.model_specials,
                context=f"equipment '{eq.name}' model specials",
            )
            if eq.assault is not None:
                _validate_specials(
                    spawns_keys,
                    eq.assault.specials,
                    context=f"equipment '{eq.name}' assault specials",
                )
            if eq.range is not None:
                _validate_specials(
                    spawns_keys,
                    eq.range.specials,
                    context=f"equipment '{eq.name}' range specials",
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


def race_slots(race: RaceConfig) -> Iterator[Specials]:
    """Yield every Slot a Race holds instances in, whatever record carries it.

    The one walk over a Race's Specials (ADR 0024). It lists the Slots by
    hand because the schema names them by hand, so widening the schema and
    widening the walk are the same edit.
    """
    for unit in race.units.values():
        yield unit.specials
    for model in race.models.values():
        yield from (model.unit_specials, model.specials, model.assault.specials)
    for equipment in race.equipment.values():
        yield from (equipment.unit_specials, equipment.model_specials)
        if equipment.assault is not None:
            yield equipment.assault.specials
        if equipment.range is not None:
            yield equipment.range.specials
