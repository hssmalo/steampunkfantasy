"""What the simulator is asked: one Unit, its Damage tables, and a starting state."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast, get_args

from spf.schemas.type_aliases import DamageTableName
from spf.sim.dice import Dice
from spf.sim.effects import STRENGTH_REQUIRED, PlaceToken
from spf.sim.tables import CompiledTable

GRAMMAR = """\
A comma-separated list. A roll is a dice expression, landing on the chosen table
(`d6`, `2d4-1`), or prefixed by a table (`psychic:d6`). `--start` also takes
`future=N` and `future_crew=N`, `bleed=N` and `poison=N` for one Token of that
strength, `<token>=N` for N Tokens, and a bare `<token>` for one: `fire=2`,
`shaken`. Example: "regular:d6, bleed=4, future=2"."""

_TABLES: list[str] = list(get_args(DamageTableName.__value__))
_NAME = re.compile(r"[a-z][a-z_]*")


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
    and `acid`, each kind holding every Instance's strength, which add up.
    `incoming` holds the hits that land every Round, if any; without them a run
    ends with the Unit's Continuing Damage.
    `points` is the Unit's Points at its default loadout, `None` when it has no
    Cost.
    """

    unit: str
    models: int
    points: int | None = None
    tables: Mapping[DamageTableName, CompiledTable]
    start: Start = field(default_factory=Start)
    incoming: list[Hit] = field(default_factory=list)
    resistance: Mapping[str, list[Dice]] = field(default_factory=dict)
    endurance: int = 0
    max_rounds: int = 20


def _items(text: str) -> list[str]:
    """Split a comma-separated list, dropping empty items."""
    return [item.strip() for item in text.split(",") if item.strip()]


def _hit(item: str, *, table: DamageTableName, option: str) -> Hit | None:
    """Read one roll, or `None` if the item is not shaped like one."""
    named, colon, dice = item.rpartition(":")
    if colon:
        spelled = named.strip().capitalize()
        if spelled not in _TABLES:
            msg = f"{option}: {named.strip()!r} is not a Damage table: {_TABLES}"
            raise ValueError(msg)
        return Hit(dice=Dice.parse(dice), table=cast("DamageTableName", spelled))
    try:
        return Hit(dice=Dice.parse(item), table=table)
    except ValueError:
        return None


def parse_hits(text: str, *, table: DamageTableName) -> list[Hit]:
    """Read `--incoming`: rolls only."""
    hits = []
    for item in _items(text):
        if (hit := _hit(item, table=table, option="--incoming")) is None:
            msg = f"--incoming: {item!r} is not a roll"
            raise ValueError(msg)
        hits.append(hit)
    return hits


def parse_start(text: str, *, table: DamageTableName) -> Start:
    """Read `--start`: rolls, Future Damage and Tokens (see `GRAMMAR`)."""
    hits: list[Hit] = []
    tokens: list[PlaceToken] = []
    future = {"future": 0, "future_crew": 0}
    for item in _items(text):
        if "=" not in item and (hit := _hit(item, table=table, option="--start")):
            hits.append(hit)
            continue
        name, _, value = (part.strip() for part in item.partition("="))
        if not _NAME.fullmatch(name) or (value and not value.isdigit()):
            msg = f"--start: cannot read {item!r}"
            raise ValueError(msg)
        if name in future:
            future[name] += int(value or 1)
        elif name in STRENGTH_REQUIRED:
            if not value:
                msg = f"--start: {name} needs a strength, like {name}=4"
                raise ValueError(msg)
            tokens.append(PlaceToken(name=name, strength=int(value)))
        else:
            tokens.extend(PlaceToken(name=name) for _ in range(int(value or 1)))
    return Start(
        hits=hits,
        tokens=tokens,
        future=future["future"],
        future_crew=future["future_crew"],
    )
