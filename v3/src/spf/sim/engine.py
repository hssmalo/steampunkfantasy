"""One simulated run: a Unit's state, changed row by row and Round by Round."""

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, Protocol

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
from spf.sim.tables import NoteRules

type EndedBy = Literal["destroyed", "no continuing damage", "max rounds"]

MIN_STRENGTH = 4
"""The weakest Bleed or Poison: `[4]`."""

MAX_STRENGTH = 12
"""The strongest Bleed or Poison: `[12]`."""

STRENGTH_STEP = 2
"""How far one downgrade or amplification moves a strength: 4, 6, 8, 10, 12."""

FIRE_OUT = 2
"""A Fire roll at or below this, after fire resistance, puts the Fire out."""

BLEED_STOPS = 2
"""A Bleed roll at or below this removes the Bleed (`token.bleed`)."""

MINOR_ACID_HOLDS = 3
"""A Minor Acid roll at or above this adds Future Damage; below it, it is removed."""

ACID_ROLLS_AGAIN = 8
"""The Acid result that rolls three more times on the acid table."""

ACID_SPILLS = {
    4: "poison cloud[4] and minor acid to other Units in the hex",
    5: "minor acid to Units within range 2",
}
"""Acid results whose effect lands beyond this Unit, from `token.acid`."""

TERROR_SPILLS = "terror on friendly Units"

_COUNTED_CONTINUING = ["fire", "acid", "minor_acid"]
"""Continuing Damage Tokens without a strength, tracked as plain counts."""

_RESISTED_BY = {"Regular": "regular", "Psychic": "psychic"}
"""The resistance that reduces a hit on each Damage table, where one does."""


@dataclass(frozen=True, kw_only=True)
class Cause:
    """What made a Damage table roll, and how to roll the same damage again."""

    source: Literal["hit", "fire", "poison", "bleed"]
    roll: Callable[[], int]


def _amplified(strength: int) -> int:
    """Step one Bleed up a size, capped at the strongest; 0 stays removed."""
    return min(strength + STRENGTH_STEP, MAX_STRENGTH) if strength else 0


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
        """Freeze the state as the report sees it.

        Bleed and Poison are counted per strength, as `bleed[4]`, since a
        smaller die stops or fades sooner.
        """
        tokens = Counter(self.counters)
        tokens.update(f"bleed[{strength}]" for strength in self.bleeds if strength)
        tokens.update(f"poison[{strength}]" for strength in self.poisons if strength)
        return Snapshot(
            models=0 if self.destroyed else self.models,
            future=self.future,
            future_crew=self.future_crew,
            tokens=+tokens,
        )


class Policy(Protocol):
    """The player's choices during a run, kept apart so they can be swapped."""

    def spend_endurance(self, state: UnitState) -> bool:
        """Decide whether to spend an Endurance Token to save a dying Model."""
        ...


class FixedPolicy:
    """Always spend Endurance when it is legal; never heal or repair."""

    def spend_endurance(self, state: UnitState) -> bool:
        """Spend Endurance whenever the Unit has some."""
        return state.counters["endurance"] > 0


@dataclass(kw_only=True)
class _Run:
    """The mutable working of one run; `run_once` is its only caller."""

    scenario: Scenario
    roller: Roller
    state: UnitState
    notes: NoteRules
    """What every one of the Unit's table notes says, taken together."""
    policy: Policy
    saved_bleed: bool = False
    """Whether Endurance saved a Model from the Bleed now rolling."""
    rolling_bleed: int | None = None
    """Where in `state.bleeds` the Bleed now rolling sits, so it can be Raised."""
    table_rolls: Counter[DamageTableName] = field(default_factory=Counter)
    missing_tables: Counter[DamageTableName] = field(default_factory=Counter)
    spillover: Counter[str] = field(default_factory=Counter)
    unparsed: Counter[tuple[DamageTableName, str, str]] = field(default_factory=Counter)
    kills: int = 0
    """Models killed so far, so a Token can tell whether its damage killed one."""

    def resisted(self, dice: Dice, table: DamageTableName) -> int:
        """Roll a hit's damage, less the resistance that table's damage meets."""
        return dice.roll(self.roller) - self.resistance(_RESISTED_BY.get(table, ""))

    def hit(self, hit: Hit) -> None:
        """Resolve one landed hit."""
        cause = Cause(source="hit", roll=lambda: self.resisted(hit.dice, hit.table))
        self.roll_on(hit.table, cause.roll(), cause=cause)

    def roll_on(self, table: DamageTableName, value: int, *, cause: Cause) -> None:
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
        for note in compiled.notes.unparsed:
            self.unparsed[table, "note", note] += 1
        row = compiled.row_for(value)
        if row is None:
            return
        for effect in row.effects:
            if state.destroyed:
                return
            self.apply(effect, table=table, label=row.label, cause=cause)

    def apply(
        self, effect: Effect, *, table: DamageTableName, label: str, cause: Cause
    ) -> None:
        """Apply one effect of a row."""
        state = self.state
        match effect:
            case Kill():
                self.kill(effect, table=table, cause=cause)
            case FutureDamage(amount=amount):
                state.future += amount
            case FutureCrewDamage(amount=amount):
                state.future_crew += amount
            case PlaceToken():
                self.place(effect, cause=cause)
            case UnitDestroyed():
                state.destroyed = True
            case AmplifyBleeding(only_from_bleeding=only_from_bleeding):
                if cause.source == "bleed" or not only_from_bleeding:
                    state.bleeds[:] = [
                        _amplified(strength) for strength in state.bleeds
                    ]
            case DamageOn() | RollAgain():
                self.roll_further(effect, table=table, cause=cause)
            case _:
                self.record(effect, table=table, label=label)

    def kill(self, effect: Kill, *, table: DamageTableName, cause: Cause) -> None:
        """Kill Models one at a time, or replace a kill once every Model is down."""
        for _ in range(effect.count):
            if self.state.models > 0:
                self.kill_one(cause=cause, temporary=effect.temporary)
                continue
            for instead in self.notes.replace_kill_when_all_down:
                self.apply(instead, table=table, label="note", cause=cause)

    def roll_further(
        self, effect: DamageOn | RollAgain, *, table: DamageTableName, cause: Cause
    ) -> None:
        """Roll again, on another Damage table or on this one."""
        match effect:
            case DamageOn(dice=dice, table=other):
                onward = Cause(
                    source=cause.source, roll=lambda: self.resisted(dice, other)
                )
                self.roll_on(other, onward.roll(), cause=onward)
            case RollAgain(times=times):
                for _ in range(times):
                    if not self.state.destroyed:
                        self.roll_on(table, cause.roll(), cause=cause)

    def record(self, effect: Effect, *, table: DamageTableName, label: str) -> None:
        """Count an effect the run does not follow."""
        match effect:
            case Spillover(text=text):
                self.spillover[text] += 1
            case Unparsed(text=text):
                self.unparsed[table, label, text] += 1
            case RowReference():
                self.unparsed[table, label, str(effect)] += 1

    def kill_one(self, *, cause: Cause, temporary: bool = False) -> None:
        """Kill one Model; the last one takes the Unit with it, unless temporary.

        Spending Endurance instead gives the Unit Bleed[4], or keeps the Bleed
        that was killing at Bleed[4], and Future Damage is not halved
        (`token.endurance`).
        """
        state = self.state
        if state.counters["endurance"] and self.policy.spend_endurance(state):
            state.counters["endurance"] -= 1
            if cause.source == "bleed":
                self.saved_bleed = True
            else:
                state.bleeds.append(MIN_STRENGTH)
            return
        self.kills += 1
        self.state.models -= 1
        if self.notes.halve_future_on_kill:
            self.state.future //= 2
        if self.state.models <= 0 and not temporary:
            self.state.destroyed = True

    def place(self, token: PlaceToken, *, cause: Cause | None = None) -> None:
        """Place one Token.

        Shaken is placed twice on a Unit that has none (`explanation` in
        `rules/tokens.toml`).
        """
        state = self.state
        if token.name in self.notes.immune:
            return
        from_bleed = cause is not None and cause.source == "bleed"
        if token.name == "bleed" and from_bleed:
            if token.strength and self.rolling_bleed is not None:
                bleeds = state.bleeds
                index = self.rolling_bleed
                bleeds[index] = max(bleeds[index], token.strength)
            return
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
            if roll <= BLEED_STOPS:
                bleeds[index] = 0
                continue
            strength = bleeds[index]
            cause = Cause(
                source="bleed",
                roll=lambda strength=strength: self.roller.roll(strength),
            )
            kills, self.saved_bleed = self.kills, False
            self.rolling_bleed = index
            self.roll_on("Regular", roll, cause=cause)
            self.rolling_bleed = None
            if self.kills > kills:
                bleeds[index] = 0
            elif self.saved_bleed:
                bleeds[index] = MIN_STRENGTH
        self.state.bleeds = [strength for strength in bleeds if strength]

    def agony_poison(self) -> None:
        """Agony 3: each Poison rolls, then goes or downgrades (`token.poison`)."""
        poisons = self.state.poisons
        for index in range(len(poisons)):
            if self.state.destroyed:
                return
            if not poisons[index]:
                continue
            strength = poisons[index]
            cause = Cause(
                source="poison",
                roll=lambda strength=strength: (
                    self.roller.roll(strength) - self.resistance("poison")
                ),
            )
            kills = self.kills
            self.roll_on("Regular", cause.roll(), cause=cause)
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
        """Roll an Acid or Minor Acid die, less acid resistance."""
        return self.roller.roll(sides) - self.resistance("acid")

    def acid_result(self, result: int) -> None:
        """Apply one result of the acid table; each row is the one below plus more."""
        state = self.state
        if result < 1:
            return
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
            (4, lambda: self.place(PlaceToken(name="minor_acid"))),
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
        cause = Cause(
            source="fire", roll=lambda: self.roller.roll(6) - self.resistance("fire")
        )
        rolls = [cause.roll() for _ in range(counters["fire"])]
        burning = [roll for roll in rolls if roll > FIRE_OUT]
        counters["fire"] = len(burning)
        for roll in burning:
            if self.state.destroyed:
                return
            self.roll_on("Regular", roll, cause=cause)

    def resistance(self, kind: str) -> int:
        """Roll the Unit's resistance against one damage type; 0 if it has none."""
        return sum(
            dice.roll(self.roller) for dice in self.scenario.resistance.get(kind, [])
        )

    def incoming(self) -> None:
        """Land this Round's incoming hits, ahead of the Agony Phases."""
        for hit in self.scenario.incoming:
            if self.state.destroyed:
                return
            self.hit(hit)

    def play_round(self) -> None:
        """Play one Round: incoming hits, then the Agony Phases in order."""
        phases = [
            self.incoming,
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


def _merged_notes(scenario: Scenario) -> NoteRules:
    """Take every table's notes together: they describe one Unit."""
    notes = [table.notes for table in scenario.tables.values()]
    return NoteRules(
        halve_future_on_kill=any(note.halve_future_on_kill for note in notes),
        immune=frozenset().union(*(note.immune for note in notes)),
        replace_kill_when_all_down=next(
            (
                note.replace_kill_when_all_down
                for note in notes
                if note.replace_kill_when_all_down
            ),
            (),
        ),
    )


def run_once(
    scenario: Scenario, roller: Roller, *, policy: Policy | None = None
) -> RunResult:
    """Simulate one run of a Scenario: the starting hits, then Rounds.

    A run stops when the Unit is destroyed, when no Continuing Damage remains,
    or at the Scenario's Round cap.
    """
    start = scenario.start
    run = _Run(
        scenario=scenario,
        roller=roller,
        notes=_merged_notes(scenario),
        policy=policy or FixedPolicy(),
        state=UnitState(
            models=scenario.models, future=start.future, future_crew=start.future_crew
        ),
    )
    state = run.state
    state.counters["endurance"] = scenario.endurance
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
        if not (state.continuing or scenario.incoming):
            ended_by = "no continuing damage"
            break
        if rounds == scenario.max_rounds:
            break
        rounds += 1
        run.play_round()
        snapshots.append(state.snapshot())
    return run.result(rounds=rounds, ended_by=ended_by, snapshots=snapshots)
