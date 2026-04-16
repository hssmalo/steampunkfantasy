"""Resolved Unit data structure with self-contained effective properties."""

from dataclasses import dataclass, field

from spf.armies.model import Model
from spf.schemas import type_aliases as t
from spf.schemas.race import UnitConfig


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
        num_models = len(self.models)
        for i, model in enumerate(self.models):
            # Model is an upgrade when its name differs from the default slot
            if model.name != self.config.models[i] and model.config.cost:
                cost = cost + model.config.cost
            for equip in model.upgrade_equipment:
                if equip.cost is None:
                    continue
                if equip.upgrade_all is False:
                    # Per-model pricing: multiply by full unit size
                    cost = cost + equip.cost * num_models
                else:
                    cost = cost + equip.cost
        return cost
