"""Resolved Unit data structure with self-contained effective properties."""

from dataclasses import dataclass, field
from typing import get_args

from spf.armies.model import Model
from spf.schemas import type_aliases as t
from spf.schemas.race import OrdersConfig, UnitConfig

# Canonical Speed ordering for stable merged-order output.
_SPEED_ORDER: tuple[t.Speed, ...] = get_args(t.Speed.__value__)


@dataclass(frozen=True)
class Unit:
    """A fully resolved unit instance: all equipment configs are stored directly.

    After construction no race_config is needed for any computation.
    """

    name: str
    config: UnitConfig = field(repr=False)
    models: tuple[Model, ...]

    @property
    def unit_specials(self) -> dict[t.UnitSpecial, str]:
        """Stacked unit-level specials: unit config then each model's unit_specials."""
        result: dict[t.UnitSpecial, str] = dict(self.config.special)
        for model in self.models:
            result |= model.unit_specials
        return result

    def cost(self) -> t.Cost:
        """Full unit cost: base + upgrade model costs + equipment costs.

        For upgrade_all=False equipment, cost is multiplied by the total number of
        models in the unit (per-model pricing charged at unit granularity).
        """
        cost = self.config.cost or t.Cost()

        unique = []
        for i, model in enumerate(self.models):
            # Model is an upgrade when its name differs from the default slot
            if model.name != self.config.models[i] and model.config.cost:
                cost = cost + model.config.cost
            for equip in model.upgrade_equipment:
                if equip.cost is None:
                    continue
                if not equip.upgrade_all:
                    cost = cost + equip.cost
                elif equip.name in unique:
                    continue
                else:
                    unique.append(equip.name)
                    cost = cost + equip.cost
        return cost

    def orders(self) -> OrdersConfig:
        """Return base orders unioned with each effective equipment's orders_gained.

        Per order-type (fire/movement) and per Speed: base rows first, then each
        equipment's gained rows, dropping exact-duplicate rows. Speeds present
        only in equipment appear too. Speeds are ordered by the canonical Speed
        literal order. Source configs are never mutated.
        """
        gained = [
            equip.orders_gained
            for model in self.models
            for equip in model.equipment
            if equip.orders_gained is not None
        ]
        return OrdersConfig(
            fire=self._merge_order_type(self.config.orders.fire, gained, "fire"),
            movement=self._merge_order_type(
                self.config.orders.movement, gained, "movement"
            ),
        )

    @staticmethod
    def _merge_order_type(
        base: dict[t.Speed, list[list[str]]] | None,
        gained: list[OrdersConfig],
        kind: str,
    ) -> dict[t.Speed, list[list[str]]] | None:
        """Merge one order-type across base and each equipment's gained orders."""
        base = base or {}
        gained_maps = [getattr(g, kind) or {} for g in gained]
        speeds = {*base, *(s for g in gained_maps for s in g)}
        merged: dict[t.Speed, list[list[str]]] = {}
        for speed in _SPEED_ORDER:
            if speed not in speeds:
                continue
            rows: list[list[str]] = [list(row) for row in base.get(speed, [])]
            for gained_map in gained_maps:
                for row in gained_map.get(speed, []):
                    if list(row) not in rows:
                        rows.append(list(row))
            merged[speed] = rows
        return merged or None
