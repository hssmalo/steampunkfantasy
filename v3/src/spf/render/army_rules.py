"""Army Reference view-model: shape a resolved Army into a nested rules view.

This is a *presentation* transposition (ADR 0007), like `spf.render.cards`.
It reads the resolved `Army` and, for the name and signature of every Special
instance on it, the rule registries (ADR 0024) — no `race_config`, no full
special-rule text (that belongs to the Rulebook product). No templates.

Its one touch of disk is the `ImageLookup` from `spf.render.images`, which asks
the committed Asset store whether a Target has art (ADR 0017); it is injected,
so a test can build a reference without a filesystem at all.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from spf.armies.army import Army
from spf.armies.model import Model
from spf.armies.unit import Unit
from spf.registry import load_registry
from spf.render import rules_reference
from spf.render.images import ImageLookup, committed_image
from spf.render.rules_reference import RulesReference
from spf.render.specials import SpecialLine, special_lines
from spf.schemas import type_aliases as t
from spf.schemas.race import EquipmentConfig

type _Specials = list[SpecialLine]


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
    note: str
    assault_note: str
    equipment_notes: list[tuple[str, str]]
    """(Equipment name, note) for each rangeless Equipment carrying one.

    A rangeless Equipment gets no sub-entry of its own, so its note is printed
    against the Model carrying it and labeled with the Equipment's name.
    """

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
    note: str


@dataclass(frozen=True)
class UnitEntry:
    """One distinct Unit configuration, with a count of identical duplicates."""

    name: str
    image: Path | None
    count: int
    size: str
    model_summary: list[str]
    types: list[t.ModelType]
    armor: list[int] | None
    points: int
    shaken_speed: str
    shaken_movement: list[str]
    shaken_fire: str
    specials: _Specials
    note: str
    damage_tables: list[tuple[str, list[tuple[str, str]], list[str]]]
    models: list[ModelEntry]


@dataclass(frozen=True)
class ArmyReference:
    """The whole Army's reference document: title block plus distinct Units."""

    stem: str
    nick: str
    race: t.RaceName
    race_image: Path | None
    points: int
    units: list[UnitEntry]
    rules: RulesReference | None = None
    """The Rules Reference printed after the Units; `None` under `--no-rules`."""


type _AnchorFor = Callable[[str], str | None] | None
"""Resolves a Special Identifier to its Rules Reference entry, or nothing."""


def _equipment_entry(
    equip: EquipmentConfig, *, anchor_for: _AnchorFor
) -> EquipmentEntry:
    assert equip.range is not None  # noqa: S101  guarded by caller
    return EquipmentEntry(
        name=equip.name,
        range=equip.range.range,
        angle=list(equip.range.angle),
        damage=equip.range.damage,
        ap=equip.range.ap,
        specials=special_lines(equip.range.specials, anchor_for=anchor_for),
        note=equip.range.note,
    )


def _dedup[T](entries: Sequence[T]) -> list[T]:
    """Drop duplicate entries, preserving first-seen order."""
    result: list[T] = []
    for entry in entries:
        if entry not in result:
            result.append(entry)
    return result


def _model_entry(model: Model, *, anchor_for: _AnchorFor) -> ModelEntry:
    ranged_equipment = [equip for equip in model.equipment if equip.range is not None]
    assault = model.assault()
    return ModelEntry(
        name=model.display_name,
        equipment_summary=_count_summary(model.equipment, lambda e: e.name),
        specials=special_lines(model.model_specials, anchor_for=anchor_for),
        assault_strength=list(assault.strength),
        assault_strength_die=assault.strength_die,
        assault_deflection=list(assault.deflection),
        assault_deflection_die=assault.deflection_die,
        assault_damage=assault.damage,
        assault_ap=assault.ap,
        assault_specials=special_lines(assault.specials, anchor_for=anchor_for),
        note=model.config.note,
        assault_note=assault.note,
        equipment_notes=_dedup(
            [
                (equip.name, equip.note)
                for equip in model.equipment
                if equip.note and equip.range is None
            ]
        ),
        equipment=_dedup(
            [_equipment_entry(e, anchor_for=anchor_for) for e in ranged_equipment]
        ),
    )


def _unit_entry(
    unit: Unit, *, race: t.RaceName, image_for: ImageLookup, anchor_for: _AnchorFor
) -> UnitEntry:
    return UnitEntry(
        name=unit.display_name,
        # `unit.name` is the TOML key, which is what addresses an Asset;
        # `unit.display_name` above is the player's Nick or the catalogue name.
        image=image_for(race, unit.name),
        count=1,
        size=load_registry().display_name(f"size.{unit.config.size}"),
        model_summary=_count_summary(unit.models, lambda m: m.display_name),
        types=unit.common_types,
        # `unit.armor`, not `unit.config.armor`: a Model or an Equipment may
        # raise a Unit's armor, and the grant is only visible in the stacked
        # value (ADR 0024).
        armor=list(unit.armor) if unit.armor is not None else None,
        points=unit.cost().to_points(),
        shaken_speed=unit.config.shaken.speed,
        shaken_movement=list(unit.config.shaken.movement_order),
        shaken_fire=unit.config.shaken.fire_order,
        specials=special_lines(unit.unit_specials, anchor_for=anchor_for),
        note=unit.config.note,
        damage_tables=[
            (
                name,
                [(_roll_text(row.roll), row.effect) for row in table.rows],
                list(table.notes),
            )
            for name, table in unit.config.damage_tables.items()
        ],
        models=_dedup(
            [_model_entry(model, anchor_for=anchor_for) for model in unit.models]
        ),
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


def build_reference(
    army: Army,
    *,
    stem: str,
    image_for: ImageLookup = committed_image,
    rules: bool = True,
    anchor_prefix: str = "",
) -> ArmyReference:
    """Build an `ArmyReference` from a resolved Army.

    `image_for` resolves Image Assets; it defaults to the committed store and
    is swapped for `no_image` by `--no-images`. A Target with no committed art
    simply gets `None` — the templates then emit nothing, leaving "what is
    missing" to the Survey (ADR 0011).

    The Rules Reference is built first, so the Unit lines take their anchors
    from the very entries they link to and the two cannot disagree.
    `anchor_prefix` namespaces those anchors, which an Army Pack needs because
    it is one document with one id space.
    """
    reference = (
        rules_reference.build(army, registry=load_registry(), prefix=anchor_prefix)
        if rules
        else None
    )
    anchor_for = reference.anchor_for if reference is not None else None
    return ArmyReference(
        stem=stem,
        nick=army.nick,
        race=army.race,
        # The race Target's name is the race name itself.
        race_image=image_for(army.race, army.race),
        points=army.cost().to_points(),
        units=_collapse_units(
            [
                _unit_entry(
                    unit, race=army.race, image_for=image_for, anchor_for=anchor_for
                )
                for unit in army.units
            ]
        ),
        rules=reference,
    )
