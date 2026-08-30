"""Race Overview view-model: shape a whole Race catalogue into a flat view.

A *presentation* transposition (ADR 0007) over the **unresolved** `RaceConfig`,
the way `spf.render.army_rules` is one over a resolved Army. Nothing here is
fielded, so nothing here is stacked: a `Stacker` stays the delta it was
declared as (`spf.render.declarations`), because a Model's armor grant has no
value until a specific Unit is fielded under it.

The sections are flat and cross-linked rather than nested (ADR 0031). A fielded
Army has one chosen path through Unit, Model and Equipment; a Race is an N:M
web, so every record appears exactly once and is addressed by an anchor other
records link to.

Its one touch of disk is the `ImageLookup` from `spf.render.images`, which asks
the committed Asset store whether a Target has art (ADR 0017); it is injected,
so a test can build an overview without a filesystem at all.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import get_args

from spf.registry import load_registry
from spf.render.anchors import slug
from spf.render.costs import cost_columns, cost_text
from spf.render.damage import roll_text
from spf.render.images import ImageLookup, committed_image
from spf.render.orders import Rows, flat_rows
from spf.render.specials import SpecialLine, special_lines
from spf.schemas import type_aliases as t
from spf.schemas.race import EquipmentConfig, ModelConfig, RaceConfig, UnitConfig

UNIT = "unit"
MODEL = "model"
EQUIPMENT = "equipment"
SPAWN = "spawn"
"""The section prefixes every anchor is namespaced under."""

# The `ModelType` literal's order is the canonical order a Type line prints in,
# as `spf.schemas.type_aliases` states where it declares it.
_MODEL_TYPE_ORDER: list[t.ModelType] = list(get_args(t.ModelType.__value__))

type _AnchorFor = Callable[[str], str | None] | None
"""Resolves a Special Identifier to its Rules Reference entry, or nothing."""

type _Priced = UnitConfig | ModelConfig | EquipmentConfig
"""The record kinds a `Cost` orders (ADR 0026)."""


def anchor(section: str, key: str) -> str:
    """Address one record by its section and its TOML key.

    The key rather than the display name: it is unique within its section and
    survives a rename. The section prefix is what resolves the one genuine
    cross-section collision — `dwarf_infantry` is both a Unit key and a Model
    key — by construction, rather than by a counter that would shift every
    later anchor the moment a record is added.
    """
    return f"{section}-{slug(key)}"


@dataclass(frozen=True)
class RaceLink:
    """A pointer at another record of this catalogue: what to call it, and where.

    The anchor travels beside the name rather than as a finished link, as
    `SpecialLine` and `RuleLink` already do: the Markdown and LaTeX families
    need different link syntax from the same value.
    """

    name: str
    anchor: str


@dataclass(frozen=True)
class UnitEntry:
    """One catalogue Unit: what it costs, what it fields, and how it moves."""

    key: str
    name: str
    anchor: str
    image: Path | None
    lore: str
    tip: str
    cost: str
    cost_columns: list[str]
    points: int
    size: str
    armor: list[int] | None
    """The Unit's own declaration. A Model or an Equipment raising it says so
    on its own entry, as a declared delta; nothing is stacked here."""

    types: list[t.ModelType]
    models: list[RaceLink]
    model_count: int
    specials: list[SpecialLine]
    shaken_speed: str
    shaken_movement: list[str]
    shaken_fire: str
    movement_rows: Rows
    fire_rows: Rows
    damage_tables: list[tuple[str, list[tuple[str, str]], list[str]]]
    note: str


@dataclass(frozen=True)
class RaceOverview:
    """A Race's whole catalogue: its title block, then its flat sections."""

    stem: str
    race: t.RaceName
    title: str
    description: str
    """The Race's own description — a record's is the image-generation prompt
    and is printed nowhere, but this one is the Race's front matter."""

    race_image: Path | None
    units: list[UnitEntry]


@dataclass(frozen=True)
class _Catalogue:
    """What shaping any entry needs: the Race, its records, and the two seams.

    Threaded as one value because every section reads the same four things,
    and a cross-link resolves against records the entry itself does not hold.
    """

    race: t.RaceName
    config: RaceConfig
    image_for: ImageLookup
    anchor_for: _AnchorFor


def _in_cost_order[T: _Priced](records: dict[str, T]) -> list[tuple[str, T]]:
    """Order records by `Cost.sort_idx`, TOML declaration order breaking ties.

    What `spf race things` lists, and a conscious choice: the sort groups
    records that read together, because of how pricing works. `sorted` is
    stable, so the declaration order the TOML file was authored in survives a
    tie with no second key.
    """
    return sorted(
        records.items(), key=lambda item: item[1].cost.sort_idx if item[1].cost else 0
    )


def _common_types(roster: Sequence[ModelConfig]) -> list[t.ModelType]:
    """Return the Types every Model of a roster shares, canonically ordered.

    A catalogue Unit has no Types of its own — `type` is a Model's field — so
    what a Unit can be said to be is what all of its Models are. Empty when
    they share nothing, matching the resolved Army's Type line.
    """
    if not roster:
        return []
    shared = set(roster[0].type)
    for model in roster[1:]:
        shared &= set(model.type)
    return [kind for kind in _MODEL_TYPE_ORDER if kind in shared]


def _model_links(keys: Sequence[str], models: dict[str, ModelConfig]) -> list[RaceLink]:
    """Link each distinct Model of a roster once, in declaration order.

    A roster names one Model per slot, so a Unit of four identical Models
    names it four times; the entry linked to is the same one each time.
    """
    seen: dict[str, None] = {}
    for key in keys:
        seen[key] = None
    return [RaceLink(name=models[key].name, anchor=anchor(MODEL, key)) for key in seen]


def _unit_entry(key: str, unit: UnitConfig, *, catalogue: _Catalogue) -> UnitEntry:
    """Shape one catalogue Unit into its entry."""
    models = catalogue.config.models
    return UnitEntry(
        key=key,
        name=unit.name,
        anchor=anchor(UNIT, key),
        # The TOML key is what addresses an Asset; `unit.name` is what a
        # reader is shown.
        image=catalogue.image_for(catalogue.race, key),
        lore=unit.lore,
        tip=unit.tip,
        cost=cost_text(unit.cost),
        cost_columns=cost_columns(unit.cost),
        # The Unit's own price. Fielding it costs more, but what a Model or an
        # Equipment adds is priced on that record.
        points=(unit.cost or t.Cost()).to_points(),
        size=load_registry().display_name(f"size.{unit.size}"),
        armor=list(unit.armor) if unit.armor is not None else None,
        types=_common_types([models[name] for name in unit.models]),
        models=_model_links(unit.models, models),
        model_count=len(unit.models),
        specials=special_lines(unit.specials, anchor_for=catalogue.anchor_for),
        shaken_speed=unit.shaken.speed,
        shaken_movement=list(unit.shaken.movement_order),
        shaken_fire=unit.shaken.fire_order,
        # The Unit's own orders. An Equipment's `orders_gained` is additive
        # (ADR 0007) and prints on the Equipment, since only a fielded Unit
        # has the fixed loadout a merged table would describe.
        movement_rows=flat_rows(unit.orders.movement),
        fire_rows=flat_rows(unit.orders.fire),
        damage_tables=[
            (
                name,
                [(roll_text(row.roll), row.effect) for row in table.rows],
                list(table.notes),
            )
            for name, table in unit.damage_tables.items()
        ],
        note=unit.note,
    )


def build_overview(
    race_config: RaceConfig,
    *,
    stem: str,
    image_for: ImageLookup = committed_image,
) -> RaceOverview:
    """Build a `RaceOverview` from a Race's unresolved catalogue.

    `image_for` resolves Image Assets; it defaults to the committed store and
    is swapped for `no_image` by `--no-images`. Only the Race and its Units are
    Targets: there are no Model Assets, and `committed_image` keys on a bare
    name, so asking about a Model would answer with the Unit's art whenever the
    two share a key.
    """
    race, metadata = next(iter(race_config.races.items()))
    catalogue = _Catalogue(
        race=race, config=race_config, image_for=image_for, anchor_for=None
    )
    return RaceOverview(
        stem=stem,
        race=race,
        title=metadata.name,
        description=metadata.description,
        # The Race Target's name is the race name itself.
        race_image=image_for(race, race),
        units=[
            _unit_entry(key, unit, catalogue=catalogue)
            for key, unit in _in_cost_order(race_config.units)
        ],
    )
