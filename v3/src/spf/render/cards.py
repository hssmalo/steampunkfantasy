"""Order Card view-model: shape a resolved Army into a printable deck.

This is a *presentation* transposition (ADR 0007). The core model exposes merged
orders via `spf.armies.unit.Unit.orders`; this module turns those into the
two shapes the render families need: a flat per-Unit table (Markdown family) and
an option-index-transposed card list (LaTeX 9-per-page grid). No templates.

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
    """One order-type and one option-index for a Unit, Speeds as rows."""

    unit_name: str
    image: Path | None  # the Unit's art, printed on the back of the card
    kind: Literal["Movement", "Fire"]
    rows: _Rows  # (speed, cells) per Speed


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
            cards.append(
                OrderCard(unit_name=unit_name, image=image, kind=kind, rows=rows)
            )
    return cards


def _unit_orders(
    unit: Unit, *, race: t.RaceName, image_for: ImageLookup
) -> tuple[UnitOrders, list[OrderCard]]:
    """Build the flat table and card list for a single Unit."""
    merged = unit.orders()
    shaken = unit.config.shaken
    # `unit.name` is the TOML key, which is what addresses an Asset;
    # `unit.config.name` is the display name. One lookup serves the flat
    # table and every card the Unit produces.
    image = image_for(race, unit.name)
    unit_orders = UnitOrders(
        name=unit.config.name,
        image=image,
        size=unit.config.size,
        movement_rows=_flat_rows(merged.movement),
        fire_rows=_flat_rows(merged.fire),
        shaken_movement=[shaken.speed, *shaken.movement_order],
        shaken_fire=shaken.fire_order,
    )
    cards = [
        *_cards(unit.config.name, image=image, kind="Movement", orders=merged.movement),
        *_cards(unit.config.name, image=image, kind="Fire", orders=merged.fire),
    ]
    return unit_orders, cards


def build_deck(
    army: Army, *, stem: str, image_for: ImageLookup = committed_image
) -> OrderCardDeck:
    """Build an `OrderCardDeck` from a resolved Army.

    Each Unit contributes a flat `UnitOrders` and its transposed
    `OrderCard` set. Units producing an identical flat view (same name and
    merged movement/fire rows) collapse to one entry.

    `image_for` resolves Image Assets; it defaults to the committed store and
    is swapped for `no_image` by `--no-images`. A Unit with no committed art
    simply gets `None` — the card back then falls back to text.
    """
    units: list[UnitOrders] = []
    cards: list[OrderCard] = []
    # The dedup key stays the *display* name, deliberately: art is addressed by
    # TOML key, and no race has two Unit keys sharing a display name, so the
    # "same name, different art" collision cannot arise today.
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
