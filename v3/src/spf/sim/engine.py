"""One simulated run: a Unit's state, changed row by row and Round by Round."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Literal

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

type EndedBy = Literal["destroyed", "no continuing damage", "max rounds"]

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

    def snapshot(self) -> Snapshot:
        """Freeze the state as the report sees it."""
        return Snapshot(
            models=self.models,
            future=self.future,
            future_crew=self.future_crew,
            tokens=+self.counters,
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
        self.state.models -= 1
        if self.state.models <= 0:
            self.state.destroyed = True

    def place(self, token: PlaceToken) -> None:
        """Place one Token.

        Shaken is placed twice on a Unit that has none (`explanation` in
        `rules/tokens.toml`).
        """
        counters = self.state.counters
        if token.name == "shaken" and not counters["shaken"]:
            counters["shaken"] += 1
        counters[token.name] += 1

    def result(self, *, rounds: int, snapshots: list[Snapshot]) -> RunResult:
        """Gather the run's outcome."""
        state = self.state
        ended_by: EndedBy = "destroyed" if state.destroyed else "no continuing damage"
        return RunResult(
            destroyed=state.destroyed,
            models_lost=self.scenario.models - max(state.models, 0)
            if not state.destroyed
            else self.scenario.models,
            rounds=rounds,
            ended_by=ended_by,
            snapshots=snapshots,
            table_rolls=self.table_rolls,
            missing_tables=self.missing_tables,
            spillover=self.spillover,
            unparsed=self.unparsed,
        )


def run_once(scenario: Scenario, roller: Roller) -> RunResult:
    """Simulate one run of a Scenario: the starting hits, then Agony Phases."""
    start = scenario.start
    run = _Run(
        scenario=scenario,
        roller=roller,
        state=UnitState(
            models=scenario.models, future=start.future, future_crew=start.future_crew
        ),
    )
    for token in start.tokens:
        run.place(token)
    for hit in start.hits:
        if run.state.destroyed:
            break
        run.hit(hit)
    return run.result(rounds=0, snapshots=[run.state.snapshot()])
