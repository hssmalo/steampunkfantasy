"""Order Card view-model: shape a resolved Army into a printable deck.

This is a *presentation* transposition (ADR 0007). The core model exposes a
Unit's orders two ways: merged, via `spf.armies.unit.Unit.orders`, and split by
Order Source, via `Unit.orders_by_source`. This module turns them into the two
shapes the render families need: a flat per-Unit table off the merged view
(Markdown family) and an option-index-transposed card list, transposed once per
Order Source so no card mixes base and gained rows (LaTeX 9-per-page grid, ADR
0021). No templates.

Its one touch of disk is the `ImageLookup` from `spf.render.images`, which asks
the committed Asset store whether a Target has art (ADR 0017); it is injected,
so a test can build a deck without a filesystem at all.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from spf.armies.army import Army
from spf.armies.unit import Unit
from spf.render.images import ImageLookup, committed_image
from spf.schemas import type_aliases as t

type _Rows = list[tuple[str, list[str]]]  # (speed, cells) per row
type _Orders = dict[t.Speed, list[list[str]]] | None  # one order-type, per Speed


@dataclass(frozen=True)
class OrderCard:
    """One order-type and one option-index for one Order Source of a Unit."""

    unit_name: str
    image: Path | None  # the Unit's art, printed on the back of the card
    kind: Literal["Movement", "Fire"]
    rows: _Rows  # (speed, cells) per Speed
    equipment: str | None  # the Equipment that granted these orders; None = base


@dataclass(frozen=True)
class UnitOrders:
    """A Unit's merged orders as flat tables, for the Markdown family."""

    name: str
    image: Path | None
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
    *,
    image: Path | None,
    kind: Literal["Movement", "Fire"],
    orders: _Orders,
    equipment: str | None,
) -> list[OrderCard]:
    """Transpose one Order Source's order-type: card i = option i across Speeds."""
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
            cards.append(
                OrderCard(
                    unit_name=unit_name,
                    image=image,
                    kind=kind,
                    rows=rows,
                    equipment=equipment,
                )
            )
    return cards


def _unit_orders(
    unit: Unit, *, race: t.RaceName, image_for: ImageLookup
) -> tuple[UnitOrders, list[OrderCard]]:
    """Build the flat table and card list for a single Unit.

    The flat table is the merged view; the cards are one Card Set per Order
    Source, so a player can pull an Equipment's cards out and still hold a
    complete deck for the Unit without it (ADR 0021).

    The Asset is addressed by `unit.name`, the TOML key, not by
    `unit.display_name`, the player's Nick or the catalogue name. One lookup
    serves the flat table and every card the Unit produces.
    """
    merged = unit.orders()
    shaken = unit.config.shaken
    image = image_for(race, unit.name)
    unit_orders = UnitOrders(
        name=unit.display_name,
        image=image,
        size=unit.config.size,
        movement_rows=_flat_rows(merged.movement),
        fire_rows=_flat_rows(merged.fire),
        shaken_movement=[shaken.speed, *shaken.movement_order],
        shaken_fire=shaken.fire_order,
    )
    # Cards are transposed per Order Source, keeping each Unit's cards
    # contiguous: base Movement then Fire, then the same pair per Equipment.
    cards: list[OrderCard] = []
    for sourced in unit.orders_by_source():
        by_kind: list[tuple[Literal["Movement", "Fire"], _Orders]] = [
            ("Movement", sourced.orders.movement),
            ("Fire", sourced.orders.fire),
        ]
        for kind, orders in by_kind:
            cards.extend(
                _cards(
                    unit.display_name,
                    image=image,
                    kind=kind,
                    orders=orders,
                    equipment=sourced.source,
                )
            )
    return unit_orders, cards


def build_deck(
    army: Army, *, stem: str, image_for: ImageLookup = committed_image
) -> OrderCardDeck:
    """Build an `OrderCardDeck` from a resolved Army.

    Each Unit contributes a flat `UnitOrders` and its transposed `OrderCard`
    sets. Units producing an identical flat view (same name and merged
    movement/fire rows) collapse to one entry — every card then applies to
    every Unit sharing it, which is the invariant the collapse rests on. Two
    Units differing only by Equipment have different merged rows, so they do
    not collapse and each gets its own full set (ADR 0021). That key is the
    `display_name` — so a Nick participates in it with no special-casing, and
    differently-nicked Units each get their own card set (ADR 0019). It
    deliberately ignores the art: an Asset is addressed by TOML key, and no race
    has two Unit keys sharing a display name, so the "same name, different art"
    collision cannot arise today.

    `image_for` resolves Image Assets; it defaults to the committed store and
    is swapped for `no_image` by `--no-images`. A Unit with no committed art
    simply gets `None` — the card back then falls back to text.
    """
    units: list[UnitOrders] = []
    cards: list[OrderCard] = []
    seen: list[tuple[str, _Rows, _Rows]] = []
    for unit in army.units:
        unit_orders, unit_cards = _unit_orders(
            unit, race=army.race, image_for=image_for
        )
        key = (unit_orders.name, unit_orders.movement_rows, unit_orders.fire_rows)
        if key in seen:
            continue
        seen.append(key)
        units.append(unit_orders)
        cards.extend(unit_cards)
    return OrderCardDeck(stem=stem, units=units, cards=cards)
