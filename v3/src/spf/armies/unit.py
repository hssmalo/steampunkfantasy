"""Resolved Unit data structure with self-contained effective properties."""

from dataclasses import dataclass, field
from typing import get_args

from spf.armies.model import Model
from spf.armies.specials import merge_specials
from spf.registry import load_registry
from spf.schemas import type_aliases as t
from spf.schemas.race import OrdersConfig, UnitConfig, UnitStatModifierConfig
from spf.schemas.special import Specials


def _speed_order() -> list[str]:
    """Canonical Speed ordering for stable merged-order output.

    The declaration order of the `speed` registry, which owns the vocabulary
    (ADR 0024); re-ordering `rules/modifiers.toml` changes rendered output.
    """
    return list(load_registry().records["speed"])


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
    def unit_specials(self) -> Specials:
        """Unit-level instances: unit config then each model's contribution."""
        return merge_specials(
            self.config.specials,
            *(model.unit_specials for model in self.models),
        )

    @property
    def armor(self) -> t.Angles[int] | None:
        """Armor after every Model's and Equipment's modifier, in chain order.

        Multiplicity follows the purchase (ADR 0024). A Model-declared modifier
        applies once per Model slot declaring it; an Equipment's applies once
        for the Unit when `upgrade_all` (a fixture bought once) and once per
        Model carrying it otherwise. Only `add` multiplies — four Models each
        replacing armor with `[6,6,6,6]` can only produce `[6,6,6,6]`.
        """
        armor = None if self.config.armor is None else list(self.config.armor)
        bought: set[str] = set()
        for model in self.models:
            armor = _stack_armor(armor, model.config.unit, source=model.config.name)
            for equip in model.equipment:
                if equip.upgrade_all:
                    if equip.name in bought:
                        continue
                    bought.add(equip.name)
                armor = _stack_armor(armor, equip.unit, source=equip.name)
        return armor

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
        only in equipment appear too. Speeds are ordered by the `speed`
        registry's declaration order. Source configs are never mutated.

        This is the fold of `orders_by_source()` — one merge algorithm, two
        views (ADR 0021). The fold deduplicates *across* sources, which the
        split view deliberately does not.

        Output is unchanged from the pre-partition merge for every committed
        army. The one input that would differ is equipment encountered as A, B,
        A under two display names: the rows are the same, but A's group together
        rather than straddling B's.
        """
        sources = self.orders_by_source()
        return OrdersConfig(
            fire=_merge_across_sources([s.orders.fire for s in sources]),
            movement=_merge_across_sources([s.orders.movement for s in sources]),
        )


def _stack_armor(
    current: list[int] | None, stats: UnitStatModifierConfig | None, *, source: str
) -> list[int] | None:
    """Apply one source's armor modifier to the running value.

    A Unit with no armor of its own has no arc protected, so an `add` grants
    exactly what it adds rather than needing a base to sit on.
    """
    if stats is None or stats.armor is None:
        return current
    stacker = stats.armor
    if stacker.replace is not None:
        return list(stacker.replace)
    if stacker.add is not None:
        base = current if current is not None else [0] * len(stacker.add)
        return [a + b for a, b in zip(base, stacker.add, strict=True)]
    if stacker.extend is not None:
        msg = f"'{source}': cannot use 'extend' on unit armor; use 'add' or 'replace'"
        raise ValueError(msg)
    msg = f"'{source}': empty Stacker on unit armor"
    raise ValueError(msg)


type _SpeedRows = dict[str, list[list[str]]]


def _in_speed_order(orders: _SpeedRows | None) -> _SpeedRows:
    """Copy one order-type's rows into canonical Speed order."""
    orders = orders or {}
    return {
        speed: [list(row) for row in orders[speed]]
        for speed in _speed_order()
        if speed in orders
    }


def _new_rows(rows: list[list[str]], *, seen: list[list[str]]) -> list[list[str]]:
    """Return `rows` in order, dropping any already in `seen` or repeated here."""
    kept: list[list[str]] = []
    for row in rows:
        if list(row) not in seen and list(row) not in kept:
            kept.append(list(row))
    return kept


def _gained_rows(gained: list[_SpeedRows | None], *, base: _SpeedRows) -> _SpeedRows:
    """Union gained rows per Speed, dropping rows the base already carries."""
    merged: _SpeedRows = {}
    for speed in _speed_order():
        rows: list[list[str]] = []
        for gained_map in gained:
            rows += _new_rows(
                (gained_map or {}).get(speed, []), seen=[*base.get(speed, []), *rows]
            )
        if rows:
            merged[speed] = rows
    return merged


def _merge_across_sources(
    rows_per_source: list[_SpeedRows | None],
) -> _SpeedRows | None:
    """Concatenate one order-type across sources, dropping exact duplicates.

    The base is the first entry and is copied verbatim; only later sources are
    deduplicated against what has accumulated, which is what keeps the merged
    view byte-identical to the pre-partition merge.
    """
    first, *gained = rows_per_source
    base = first or {}
    merged: _SpeedRows = {}
    for speed in _speed_order():
        rows: list[list[str]] = [list(row) for row in base.get(speed, [])]
        for gained_map in gained:
            rows += _new_rows((gained_map or {}).get(speed, []), seen=rows)
        if rows or speed in base:
            merged[speed] = rows
    return merged or None
