"""Resolved Unit data structure with self-contained effective properties."""

from dataclasses import dataclass, field
from typing import get_args

from spf.armies.model import Model
from spf.schemas import type_aliases as t
from spf.schemas.race import OrdersConfig, UnitConfig

# Canonical Speed ordering for stable merged-order output.
_SPEED_ORDER: list[t.Speed] = list(get_args(t.Speed.__value__))

# Canonical Model Type ordering for stable common-type output. The order of the
# `ModelType` literal is meaningful: it is what the army-rules Type line is
# sorted by.
_MODEL_TYPE_ORDER: list[t.ModelType] = list(get_args(t.ModelType.__value__))


@dataclass(frozen=True)
class SourcedOrders:
    """One Order Source's contribution to a Unit's orders.

    `source` is `None` for the base Unit, else the display name of an Equipment
    that grants orders. Sources are independent because `orders_gained` is
    additive (ADR 0007), so a loadout is the base plus one entry per Equipment
    carried (ADR 0021).
    """

    source: str | None
    orders: OrdersConfig


@dataclass(frozen=True)
class Unit:
    """A fully resolved unit instance: all equipment configs are stored directly.

    After construction no race_config is needed for any computation.
    """

    name: str
    config: UnitConfig = field(repr=False)
    models: list[Model]
    nick: str | None = None

    @property
    def display_name(self) -> str:
        """The name to render: the player's Nick if set, else the catalogue name."""
        return self.nick or self.config.name

    @property
    def unit_specials(self) -> dict[t.UnitSpecial, str]:
        """Stacked unit-level specials: unit config then each model's unit_specials."""
        result: dict[t.UnitSpecial, str] = dict(self.config.special)
        for model in self.models:
            result |= model.unit_specials
        return result

    @property
    def common_types(self) -> list[t.ModelType]:
        """Types shared by every Model in the unit, in canonical ModelType order.

        Empty when the unit has no models, or when its models share no type.
        """
        if not self.models:
            return []
        shared = set(self.models[0].config.type)
        for model in self.models[1:]:
            shared &= set(model.config.type)
        return [model_type for model_type in _MODEL_TYPE_ORDER if model_type in shared]

    def cost(self) -> t.Cost:
        """Full unit cost: base + upgrade model costs + equipment costs.

        For upgrade_all=False equipment, cost is added once for each model
        in the unit (per-model pricing charged at unit granularity).

        For upgrade_all=True equipment, cost is added to the unit once
        independently of how many units are upgraded.
        """
        cost = self.config.cost or t.Cost()

        unique = []
        for i, model in enumerate(self.models):
            # Model is an upgrade when its name differs from the default slot
            if model.name != self.config.models[i] and model.config.cost:
                cost = cost + model.config.cost

            tmp = []
            for equip in model.upgrade_equipment:
                if equip.cost is None:
                    continue
                if not equip.upgrade_all:
                    cost = cost + equip.cost
                elif equip.name in unique:
                    continue
                else:
                    tmp.append(equip.name)
                    cost = cost + equip.cost
            unique = unique + tmp
        return cost

    def orders_by_source(self) -> list[SourcedOrders]:
        """Return this Unit's orders split by Order Source, base first.

        The base entry is always present. Each order-modifying equipment then
        contributes one entry, keyed by its *display* name, in first-encountered
        order across the Models. Two equipment sharing a display name union
        their rows — nothing enforces that two keys with one name (darkelf
        `hide` / `hide_free`) keep identical `orders_gained`.

        An equipment's rows are deduplicated against the base, since the base
        cards are always in the deck, but never against another equipment: the
        sources are independent and either may be absent from a loadout. An
        equipment left with no rows at all is omitted. Source configs are never
        mutated.
        """
        base_fire = _in_speed_order(self.config.orders.fire)
        base_movement = _in_speed_order(self.config.orders.movement)
        sources = [
            SourcedOrders(
                source=None,
                orders=OrdersConfig(
                    fire=base_fire or None, movement=base_movement or None
                ),
            )
        ]

        grouped: dict[str, list[OrdersConfig]] = {}
        for model in self.models:
            for equip in model.equipment:
                if equip.orders_gained is not None:
                    grouped.setdefault(equip.name, []).append(equip.orders_gained)

        for name, gained in grouped.items():
            fire = _gained_rows([g.fire for g in gained], base=base_fire)
            movement = _gained_rows([g.movement for g in gained], base=base_movement)
            if not fire and not movement:
                continue
            sources.append(
                SourcedOrders(
                    source=name,
                    orders=OrdersConfig(fire=fire or None, movement=movement or None),
                )
            )
        return sources

    def orders(self) -> OrdersConfig:
        """Return base orders unioned with each effective equipment's orders_gained.

        Per order-type (fire/movement) and per Speed: base rows first, then each
        equipment's gained rows, dropping exact-duplicate rows. Speeds present
        only in equipment appear too. Speeds are ordered by the canonical Speed
        literal order. Source configs are never mutated.

        This is the fold of `orders_by_source()` — one merge algorithm, two
        views (ADR 0021). The fold deduplicates *across* sources, which the
        split view deliberately does not.
        """
        sources = self.orders_by_source()
        return OrdersConfig(
            fire=_fold([s.orders.fire for s in sources]),
            movement=_fold([s.orders.movement for s in sources]),
        )


type _SpeedRows = dict[t.Speed, list[list[str]]]


def _in_speed_order(orders: _SpeedRows | None) -> _SpeedRows:
    """Copy one order-type's rows into canonical Speed order."""
    orders = orders or {}
    return {
        speed: [list(row) for row in orders[speed]]
        for speed in _SPEED_ORDER
        if speed in orders
    }


def _gained_rows(gained: list[_SpeedRows | None], *, base: _SpeedRows) -> _SpeedRows:
    """Union gained rows per Speed, dropping rows the base already carries."""
    merged: _SpeedRows = {}
    for speed in _SPEED_ORDER:
        rows: list[list[str]] = []
        for gained_map in gained:
            for row in (gained_map or {}).get(speed, []):
                if list(row) not in base.get(speed, []) and list(row) not in rows:
                    rows.append(list(row))
        if rows:
            merged[speed] = rows
    return merged


def _fold(sources: list[_SpeedRows | None]) -> _SpeedRows | None:
    """Concatenate one order-type across sources, dropping exact duplicates.

    The base is the first entry and is copied verbatim; only later sources are
    deduplicated against what has accumulated, which is what keeps the merged
    view byte-identical to the pre-partition merge.
    """
    first, *gained = sources
    base = first or {}
    merged: _SpeedRows = {}
    for speed in _SPEED_ORDER:
        rows: list[list[str]] = [list(row) for row in base.get(speed, [])]
        for gained_map in gained:
            for row in (gained_map or {}).get(speed, []):
                if list(row) not in rows:
                    rows.append(list(row))
        if rows or speed in base:
            merged[speed] = rows
    return merged or None
