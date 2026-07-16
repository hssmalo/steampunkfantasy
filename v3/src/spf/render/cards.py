"""Order Card view-model: shape a resolved Army into a printable deck.

This is a *presentation* transposition (ADR 0007). The core model exposes merged
orders via `spf.armies.unit.Unit.orders`; this module turns those into the
two shapes the render families need: a flat per-Unit table (Markdown family) and
an option-index-transposed card list (LaTeX 9-per-page grid). No I/O, no
templates.
"""

from dataclasses import dataclass
from typing import Literal

from spf.armies.army import Army
from spf.armies.unit import Unit
from spf.schemas import type_aliases as t

type _Rows = list[tuple[str, list[str]]]  # (speed, cells) per row
type _Orders = dict[t.Speed, list[list[str]]] | None  # one order-type, per Speed


@dataclass(frozen=True)
class OrderCard:
    """One order-type and one option-index for a Unit, Speeds as rows."""

    unit_name: str
    kind: Literal["Movement", "Fire"]
    rows: _Rows  # (speed, cells) per Speed


@dataclass(frozen=True)
class UnitOrders:
    """A Unit's merged orders as flat tables, for the Markdown family."""

    name: str
    size: str
    movement_rows: _Rows  # every (speed, cells) option, flat
    fire_rows: _Rows
    shaken_movement: list[str] | None  # speed + movement_order cells
    shaken_fire: str | None


@dataclass(frozen=True)
class OrderCardDeck:
    """The whole Army's order cards, carrying both render shapes."""

    stem: str
    units: list[UnitOrders]  # Markdown family (flat tables)
    cards: list[OrderCard]  # LaTeX family (9-per-page grid)


def _flat_rows(orders: _Orders) -> _Rows:
    """Flatten one order-type into (speed, cells) per option row, in Speed order."""
    if not orders:
        return []
    return [
        (speed, list(cells)) for speed, options in orders.items() for cells in options
    ]


def _cards(
    unit_name: str,
    kind: Literal["Movement", "Fire"],
    *,
    orders: _Orders,
) -> list[OrderCard]:
    """Transpose one order-type by option-index: card i = option i across Speeds."""
    if not orders:
        return []
    width = max(len(options) for options in orders.values())
    cards: list[OrderCard] = []
    for i in range(width):
        rows = [
            (speed, list(options[i]))
            for speed, options in orders.items()
            if i < len(options)
        ]
        if rows:
            cards.append(OrderCard(unit_name=unit_name, kind=kind, rows=rows))
    return cards


def _unit_orders(unit: Unit) -> tuple[UnitOrders, list[OrderCard]]:
    """Build the flat table and card list for a single Unit."""
    merged = unit.orders()
    shaken = unit.config.shaken
    unit_orders = UnitOrders(
        name=unit.config.name,
        size=unit.config.size,
        movement_rows=_flat_rows(merged.movement),
        fire_rows=_flat_rows(merged.fire),
        shaken_movement=[shaken.speed, *shaken.movement_order],
        shaken_fire=shaken.fire_order,
    )
    cards = [
        *_cards(unit.config.name, "Movement", orders=merged.movement),
        *_cards(unit.config.name, "Fire", orders=merged.fire),
    ]
    return unit_orders, cards


def build_deck(army: Army, *, stem: str) -> OrderCardDeck:
    """Build an `OrderCardDeck` from a resolved Army.

    Each Unit contributes a flat `UnitOrders` and its transposed
    `OrderCard` set. Units producing an identical flat view (same name and
    merged movement/fire rows) collapse to one entry.
    """
    units: list[UnitOrders] = []
    cards: list[OrderCard] = []
    seen: list[tuple[str, _Rows, _Rows]] = []
    for unit in army.units:
        unit_orders, unit_cards = _unit_orders(unit)
        key = (unit_orders.name, unit_orders.movement_rows, unit_orders.fire_rows)
        if key in seen:
            continue
        seen.append(key)
        units.append(unit_orders)
        cards.extend(unit_cards)
    return OrderCardDeck(stem=stem, units=units, cards=cards)
