"""What the simulator is asked: one Unit, its Damage tables, and a starting state."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from spf.schemas.type_aliases import DamageTableName
from spf.sim.dice import Dice
from spf.sim.effects import PlaceToken
from spf.sim.tables import CompiledTable


@dataclass(frozen=True, kw_only=True)
class Hit:
    """The damage value of an attack that has landed, rolled on one Damage table."""

    dice: Dice
    table: DamageTableName = "Regular"


@dataclass(frozen=True, kw_only=True)
class Start:
    """The state a run begins in: hits resolved before Round 1, and Tokens."""

    hits: list[Hit] = field(default_factory=list)
    tokens: list[PlaceToken] = field(default_factory=list)
    future: int = 0
    future_crew: int = 0


@dataclass(frozen=True, kw_only=True)
class Scenario:
    """One Unit in isolation, ready to be simulated.

    `resistance` is keyed by damage type: `regular`, `psychic`, `fire`, `poison`
    and `acid`. `incoming` is empty for an aftermath run and holds the hits that
    land every Round for an attrition run.
    """

    unit: str
    models: int
    tables: Mapping[DamageTableName, CompiledTable]
    start: Start = field(default_factory=Start)
    incoming: list[Hit] = field(default_factory=list)
    resistance: Mapping[str, Dice] = field(default_factory=dict)
    endurance: int = 0
    max_rounds: int = 20
