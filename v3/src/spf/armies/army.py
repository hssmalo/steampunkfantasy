"""Resolved Army data structure — the fully self-contained top-level type."""

from dataclasses import dataclass

from spf.armies.unit import Unit
from spf.schemas import type_aliases as t


@dataclass(frozen=True)
class Army:
    """A player's fully resolved force.

    All equipment configs are embedded in Unit/Model descendants.
    No race_config is needed after construction.
    """

    race: t.RaceName
    nick: str
    units: tuple[Unit, ...]

    def cost(self) -> t.Cost:
        """Return the total cost of all units in this army."""
        return sum((unit.cost() for unit in self.units), t.Cost())
