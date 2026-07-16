"""Army Reference view-model: shape a resolved Army into a nested rules view.

This is a *presentation* transposition (ADR 0007), like `spf.render.cards`.
It reads only the resolved `Army` — no `race_config`,
no rules loading, no full special-rule text (that belongs to the Rulebook
product). No I/O, no templates.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from spf.armies.army import Army
from spf.armies.model import Model
from spf.armies.unit import Unit
from spf.schemas import type_aliases as t
from spf.schemas.race import EquipmentConfig

type _Specials = list[tuple[str, str]]


def _roll_text(roll: t.DamageRoll) -> str:
    """Render a damage roll as its table-column string (`9` / `1-2` / `6+`)."""
    match roll:
        case t.ExactRoll(value=value):
            return str(value)
        case t.RangeRoll(low=low, high=high):
            return f"{low}-{high}"
        case t.AtLeastRoll(value=value):
            return f"{value}+"


def _count_summary[T](items: Sequence[T], name_of: Callable[[T], str]) -> list[str]:
    """Group `items` by equality, first-seen order, into `NxName` labels."""
    counts: list[tuple[T, int]] = []
    for item in items:
        for i, (existing, n) in enumerate(counts):
            if existing == item:
                counts[i] = (existing, n + 1)
                break
        else:
            counts.append((item, 1))
    return [f"{n}x {name_of(item)}" for item, n in counts]


@dataclass(frozen=True)
class ModelEntry:
    """One distinct Model configuration within a Unit."""

    name: str
    equipment_summary: list[str]
    specials: _Specials
    assault_strength: list[int]
    assault_strength_die: t.DieResult
    assault_deflection: list[int]
    assault_deflection_die: t.DieResult
    assault_damage: t.Die
    assault_ap: t.ArmorPenetration
    assault_specials: _Specials
    equipment: list["EquipmentEntry"]


@dataclass(frozen=True)
class EquipmentEntry:
    """One distinct ranged-equipment sub-entry within a Model."""

    name: str
    range: int
    angle: list[bool | str]
    damage: t.Die
    ap: t.ArmorPenetration
    specials: _Specials


@dataclass(frozen=True)
class UnitEntry:
    """One distinct Unit configuration, with a count of identical duplicates."""

    name: str
    count: int
    size: t.Size
    model_summary: list[str]
    armor: list[int] | None
    points: int
    shaken_speed: t.Speed
    shaken_movement: list[str]
    shaken_fire: str
    specials: _Specials
    damage_tables: list[tuple[str, list[tuple[str, str]], list[str]]]
    models: list[ModelEntry]


@dataclass(frozen=True)
class ArmyReference:
    """The whole Army's reference document: title block plus distinct Units."""

    stem: str
    nick: str
    race: t.RaceName
    points: int
    units: list[UnitEntry]


def _equipment_entry(equip: EquipmentConfig) -> EquipmentEntry:
    assert equip.range is not None  # noqa: S101  guarded by caller
    return EquipmentEntry(
        name=equip.name,
        range=equip.range.range,
        angle=list(equip.range.angle),
        damage=equip.range.damage,
        ap=equip.range.ap,
        specials=list(equip.range.special.items()),
    )


def _dedup[T](entries: Sequence[T]) -> list[T]:
    """Drop duplicate entries, preserving first-seen order."""
    result: list[T] = []
    for entry in entries:
        if entry not in result:
            result.append(entry)
    return result


def _model_entry(model: Model) -> ModelEntry:
    ranged_equipment = [equip for equip in model.equipment if equip.range is not None]
    assault = model.assault()
    return ModelEntry(
        name=model.config.name,
        equipment_summary=_count_summary(model.equipment, lambda e: e.name),
        specials=list(model.model_specials.items()),
        assault_strength=list(assault.strength),
        assault_strength_die=assault.strength_die,
        assault_deflection=list(assault.deflection),
        assault_deflection_die=assault.deflection_die,
        assault_damage=assault.damage,
        assault_ap=assault.ap,
        assault_specials=list(assault.special.items()),
        equipment=_dedup([_equipment_entry(e) for e in ranged_equipment]),
    )


def _unit_entry(unit: Unit) -> UnitEntry:
    return UnitEntry(
        name=unit.config.name,
        count=1,
        size=unit.config.size,
        model_summary=_count_summary(unit.models, lambda m: m.config.name),
        armor=list(unit.config.armor) if unit.config.armor is not None else None,
        points=unit.cost().to_points(),
        shaken_speed=unit.config.shaken.speed,
        shaken_movement=list(unit.config.shaken.movement_order),
        shaken_fire=unit.config.shaken.fire_order,
        specials=list(unit.unit_specials.items()),
        damage_tables=[
            (
                name,
                [(_roll_text(row.roll), row.effect) for row in table.rows],
                list(table.notes),
            )
            for name, table in unit.config.damage_tables.items()
        ],
        models=_dedup([_model_entry(model) for model in unit.models]),
    )


def _collapse_units(entries: Sequence[UnitEntry]) -> list[UnitEntry]:
    """Collapse units equal in every field but `count`, summing their counts."""
    collapsed: list[UnitEntry] = []
    for entry in entries:
        bare = replace(entry, count=1)
        for i, existing in enumerate(collapsed):
            if replace(existing, count=1) == bare:
                collapsed[i] = replace(existing, count=existing.count + 1)
                break
        else:
            collapsed.append(entry)
    return collapsed


def build_reference(army: Army, *, stem: str) -> ArmyReference:
    """Build an `ArmyReference` from a resolved Army."""
    return ArmyReference(
        stem=stem,
        nick=army.nick,
        race=army.race,
        points=army.cost().to_points(),
        units=_collapse_units([_unit_entry(unit) for unit in army.units]),
    )
