"""One simulated run: a Unit's state, changed row by row and Round by Round."""

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from spf.schemas.type_aliases import DamageTableName
from spf.sim.dice import Dice, Roller
from spf.sim.effects import (
    AmplifyBleeding,
    DamageOn,
    Effect,
    FutureCrewDamage,
    FutureDamage,
    Kill,
    PlaceToken,
    RollAgain,
    RowReference,
    Spillover,
    UnitDestroyed,
    Unparsed,
)
from spf.sim.scenario import Hit, Scenario

if TYPE_CHECKING:
    from collections.abc import Callable

type EndedBy = Literal["destroyed", "no continuing damage", "max rounds"]

MIN_STRENGTH = 4
"""The weakest Bleed or Poison: `[4]`."""

MAX_STRENGTH = 12
"""The strongest Bleed or Poison: `[12]`."""

STRENGTH_STEP = 2
"""How far one downgrade or amplification moves a strength: 4, 6, 8, 10, 12."""

FIRE_OUT = 1
"""A Fire roll at or below this, after fire resistance, puts the Fire out."""

MINOR_ACID_HOLDS = 3
"""A Minor Acid roll at or above this adds Future Damage; below it, it is removed."""

ACID_ROLLS_AGAIN = 8
"""The Acid result that rolls three more times on the acid table."""

ACID_SPILLS = {
    4: "poison cloud[4] and minor acid on the hex",
    5: "minor acid to Units within range 2",
}
"""Acid results whose effect lands beyond this Unit, from `token.acid`."""

TERROR_SPILLS = "terror on friendly Units"

_COUNTED_CONTINUING = ["fire", "acid", "minor_acid"]
"""Continuing Damage Tokens without a strength, tracked as plain counts."""

_RESISTED_BY = {"Regular": "regular", "Psychic": "psychic"}
"""The resistance that reduces a hit on each Damage table, where one does."""


@dataclass(frozen=True, kw_only=True)
class Snapshot:
    """The Unit at the end of a Round: Models alive and every Token count."""

    models: int
    future: int
    future_crew: int
    tokens: Counter[str]


@dataclass(frozen=True, kw_only=True)
class RunResult:
    """How one run ended, and what it rolled along the way."""

    destroyed: bool
    models_lost: int
    rounds: int
    ended_by: EndedBy
    snapshots: list[Snapshot]
    """One per Round, after the starting hits as Round 0."""
    table_rolls: Counter[DamageTableName]
    missing_tables: Counter[DamageTableName]
    spillover: Counter[str]
    unparsed: Counter[tuple[DamageTableName, str, str]]
    """Hits on unparsed text, keyed by table, row label and the text itself."""


@dataclass(kw_only=True)
class UnitState:
    """Everything a run tracks about its one Unit."""

    models: int
    destroyed: bool = False
    future: int = 0
    future_crew: int = 0
    counters: Counter[str] = field(default_factory=Counter)
    """Tokens without a strength, by id."""
    bleeds: list[int] = field(default_factory=list)
    """The strength of each Bleed; a 0 marks one removed mid-Phase."""
    poisons: list[int] = field(default_factory=list)
    """The strength of each Poison; a 0 marks one removed mid-Phase."""

    @property
    def continuing(self) -> bool:
        """Whether a Token that deals Continuing Damage remains."""
        return (
            any(self.bleeds)
            or any(self.poisons)
            or any(self.counters[token] for token in _COUNTED_CONTINUING)
        )

    def snapshot(self) -> Snapshot:
        """Freeze the state as the report sees it."""
        tokens = Counter(self.counters)
        tokens["bleed"] = sum(1 for strength in self.bleeds if strength)
        tokens["poison"] = sum(1 for strength in self.poisons if strength)
        return Snapshot(
            models=self.models,
            future=self.future,
            future_crew=self.future_crew,
            tokens=+tokens,
        )


@dataclass(kw_only=True)
class _Run:
    """The mutable working of one run; `run_once` is its only caller."""

    scenario: Scenario
    roller: Roller
    state: UnitState
    table_rolls: Counter[DamageTableName] = field(default_factory=Counter)
    missing_tables: Counter[DamageTableName] = field(default_factory=Counter)
    spillover: Counter[str] = field(default_factory=Counter)
    unparsed: Counter[tuple[DamageTableName, str, str]] = field(default_factory=Counter)
    kills: int = 0
    """Models killed so far, so a Token can tell whether its damage killed one."""

    def resisted(self, dice: Dice, table: DamageTableName) -> int:
        """Roll a hit's damage, less the resistance that table's damage meets."""
        resistance = self.scenario.resistance.get(_RESISTED_BY.get(table, ""))
        return dice.roll(self.roller) - (
            resistance.roll(self.roller) if resistance else 0
        )

    def hit(self, hit: Hit) -> None:
        """Resolve one landed hit."""
        self.roll_on(hit.table, self.resisted(hit.dice, hit.table))

    def roll_on(self, table: DamageTableName, value: int) -> None:
        """Look `value` up on a Damage table, with its Future Damage, and apply it."""
        state = self.state
        if (
            table == "Psychic"
            and state.counters["crippled_crew"]
            and state.counters["shaken"]
        ):
            table = "Crew"
        if table == "Regular":
            value += state.future
        elif table == "Crew":
            value += state.future_crew
        compiled = self.scenario.tables.get(table)
        if compiled is None:
            self.missing_tables[table] += 1
            return
        self.table_rolls[table] += 1
        row = compiled.row_for(value)
        if row is None:
            return
        for effect in row.effects:
            if state.destroyed:
                return
            self.apply(effect, table=table, label=row.label)

    def apply(self, effect: Effect, *, table: DamageTableName, label: str) -> None:
        """Apply one effect of a row."""
        state = self.state
        match effect:
            case Kill(count=count):
                for _ in range(count):
                    self.kill_one()
            case FutureDamage(amount=amount):
                state.future += amount
            case FutureCrewDamage(amount=amount):
                state.future_crew += amount
            case PlaceToken():
                self.place(effect)
            case DamageOn(dice=dice, table=other):
                self.roll_on(other, self.resisted(dice, other))
            case UnitDestroyed():
                state.destroyed = True
            case _:
                self.record(effect, table=table, label=label)

    def record(self, effect: Effect, *, table: DamageTableName, label: str) -> None:
        """Count an effect the run does not follow."""
        match effect:
            case Spillover(text=text):
                self.spillover[text] += 1
            case Unparsed(text=text):
                self.unparsed[table, label, text] += 1
            case AmplifyBleeding() | RollAgain() | RowReference():
                self.unparsed[table, label, str(effect)] += 1

    def kill_one(self) -> None:
        """Kill one Model; the last one takes the Unit with it."""
        self.kills += 1
        self.state.models -= 1
        if self.state.models <= 0:
            self.state.destroyed = True

    def place(self, token: PlaceToken) -> None:
        """Place one Token.

        Shaken is placed twice on a Unit that has none (`explanation` in
        `rules/tokens.toml`).
        """
        state = self.state
        if token.name == "bleed" and token.strength:
            state.bleeds.append(token.strength)
            return
        if token.name == "poison" and token.strength:
            state.poisons.append(token.strength)
            return
        if token.name == "shaken" and not state.counters["shaken"]:
            state.counters["shaken"] += 1
        state.counters[token.name] += 1

    def agony_bleed(self) -> None:
        """Agony 4: each Bleed rolls on its own (`token.bleed`)."""
        bleeds = self.state.bleeds
        for index in range(len(bleeds)):
            if self.state.destroyed:
                return
            if not bleeds[index]:
                continue
            roll = self.roller.roll(bleeds[index])
            if roll == 1:
                bleeds[index] = 0
                continue
            kills = self.kills
            self.roll_on("Regular", roll)
            if self.kills > kills:
                bleeds[index] = 0
        self.state.bleeds = [strength for strength in bleeds if strength]

    def agony_poison(self) -> None:
        """Agony 3: each Poison rolls, then goes or downgrades (`token.poison`)."""
        poisons = self.state.poisons
        for index in range(len(poisons)):
            if self.state.destroyed:
                return
            if not poisons[index]:
                continue
            roll = self.roller.roll(poisons[index]) - self.resistance("poison")
            kills = self.kills
            self.roll_on("Regular", roll)
            killed = self.kills > kills
            downgraded = poisons[index] - STRENGTH_STEP
            poisons[index] = 0 if killed or downgraded < MIN_STRENGTH else downgraded
        self.state.poisons = [strength for strength in poisons if strength]

    def agony_acid(self) -> None:
        """Agony 0: Terror spills onto friends, then each Acid rolls (`token.acid`)."""
        counters = self.state.counters
        if counters["terror"]:
            self.spillover[TERROR_SPILLS] += counters["terror"]
        for _ in range(counters["acid"]):
            self.acid_result(self.acid_roll(8))

    def acid_roll(self, sides: int) -> int:
        """Roll an Acid or Minor Acid die, less acid resistance, never below 1."""
        return max(1, self.roller.roll(sides) - self.resistance("acid"))

    def acid_result(self, result: int) -> None:
        """Apply one result of the acid table; each row is the one below plus more."""
        state = self.state
        if result >= ACID_ROLLS_AGAIN:
            for _ in range(3):
                self.acid_result(self.acid_roll(8))
            return
        if result == 1:
            if state.counters["acid"]:
                state.counters["acid"] -= 1
                state.counters["minor_acid"] += 1
            return
        state.future += 1
        steps: list[tuple[int, Callable[[], None]]] = [
            (3, lambda: self.place(PlaceToken(name="armor_reduced"))),
            (4, lambda: self.spill(ACID_SPILLS[4])),
            (5, lambda: self.spill(ACID_SPILLS[5])),
            (6, lambda: self.place(PlaceToken(name="terror"))),
            (7, lambda: self.place(PlaceToken(name="fire"))),
        ]
        for threshold, step in steps:
            if result >= threshold:
                step()

    def spill(self, text: str) -> None:
        """Count one spillover event."""
        self.spillover[text] += 1

    def agony_minor_acid(self) -> None:
        """Agony 1: each Minor Acid adds Future Damage or is removed."""
        counters = self.state.counters
        for _ in range(counters["minor_acid"]):
            if self.acid_roll(6) >= MINOR_ACID_HOLDS:
                self.state.future += 1
            else:
                counters["minor_acid"] -= 1

    def agony_fire(self) -> None:
        """Agony 2: every Fire rolls before any of its damage applies (`token.fire`)."""
        counters = self.state.counters
        rolls = [
            self.roller.roll(6) - self.resistance("fire")
            for _ in range(counters["fire"])
        ]
        burning = [roll for roll in rolls if roll > FIRE_OUT]
        counters["fire"] = len(burning)
        for roll in burning:
            if self.state.destroyed:
                return
            self.roll_on("Regular", roll)

    def resistance(self, kind: str) -> int:
        """Roll the Unit's resistance against one damage type; 0 if it has none."""
        dice = self.scenario.resistance.get(kind)
        return 0 if dice is None else dice.roll(self.roller)

    def play_round(self) -> None:
        """Play one Round's Agony Phases, in order."""
        phases = [
            self.agony_acid,
            self.agony_minor_acid,
            self.agony_fire,
            self.agony_poison,
            self.agony_bleed,
        ]
        for phase in phases:
            if self.state.destroyed:
                return
            phase()

    def result(
        self, *, rounds: int, ended_by: EndedBy, snapshots: list[Snapshot]
    ) -> RunResult:
        """Gather the run's outcome."""
        state = self.state
        return RunResult(
            destroyed=state.destroyed,
            models_lost=self.scenario.models
            if state.destroyed
            else self.scenario.models - state.models,
            rounds=rounds,
            ended_by=ended_by,
            snapshots=snapshots,
            table_rolls=self.table_rolls,
            missing_tables=self.missing_tables,
            spillover=self.spillover,
            unparsed=self.unparsed,
        )


def run_once(scenario: Scenario, roller: Roller) -> RunResult:
    """Simulate one run of a Scenario: the starting hits, then Rounds.

    A run stops when the Unit is destroyed, when no Continuing Damage remains,
    or at the Scenario's Round cap.
    """
    start = scenario.start
    run = _Run(
        scenario=scenario,
        roller=roller,
        state=UnitState(
            models=scenario.models, future=start.future, future_crew=start.future_crew
        ),
    )
    state = run.state
    for token in start.tokens:
        run.place(token)
    for hit in start.hits:
        if state.destroyed:
            break
        run.hit(hit)
    snapshots = [state.snapshot()]
    rounds = 0
    ended_by: EndedBy = "max rounds"
    while True:
        if state.destroyed:
            ended_by = "destroyed"
            break
        if not state.continuing:
            ended_by = "no continuing damage"
            break
        if rounds == scenario.max_rounds:
            break
        rounds += 1
        run.play_round()
        snapshots.append(state.snapshot())
    return run.result(rounds=rounds, ended_by=ended_by, snapshots=snapshots)
