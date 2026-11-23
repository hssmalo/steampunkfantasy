"""Monte Carlo over one Scenario, gathered into the report the CLI prints."""

import math
import secrets
import statistics
from collections import Counter
from dataclasses import dataclass

from spf.schemas.type_aliases import DamageTableName
from spf.sim.dice import RandomRoller
from spf.sim.engine import EndedBy, RunResult, Snapshot, run_once
from spf.sim.scenario import Scenario

_SEED_BOUND = 2**31
_P90 = 0.9


@dataclass(frozen=True, kw_only=True)
class Spread:
    """Mean, median and 90th percentile of one figure over every run."""

    mean: float
    median: float
    p90: float


@dataclass(frozen=True, kw_only=True)
class RoundSummary:
    """The mean state at the end of one Round, a finished run held at its end."""

    round: int
    models: float
    future: float
    future_crew: float
    tokens: dict[str, float]


@dataclass(frozen=True, kw_only=True)
class UnparsedHit:
    """Text the simulator could not follow, and how often a run reached it."""

    table: DamageTableName
    row: str
    """The row's printed Damage roll, or `note` for a table note."""
    text: str
    hits: int


@dataclass(frozen=True, kw_only=True)
class DamageReport:
    """What many runs of one Scenario add up to."""

    unit: str
    entry: DamageTableName
    runs: int
    seed: int
    p_destroyed: float
    points: int | None
    """The Unit's Points, `None` when it has no Cost."""
    models_lost: Spread
    rounds: dict[EndedBy, dict[int, int]]
    """How many runs ended after each number of Rounds, by how they ended."""
    ended_by: dict[EndedBy, int]
    per_round: list[RoundSummary]
    table_rolls: dict[DamageTableName, int]
    """Rolls per Damage table, the entry table first."""
    missing_tables: dict[DamageTableName, int]
    spillover: dict[str, int]
    unparsed: list[UnparsedHit]

    @property
    def expected_points_destroyed(self) -> float | None:
        """The Points an opponent expects to score: all on Unit Destroyed, else none."""
        return None if self.points is None else self.p_destroyed * self.points


def _spread(values: list[int]) -> Spread:
    """Summarize one figure; the 90th percentile is by nearest rank."""
    ordered = sorted(values)
    return Spread(
        mean=statistics.fmean(ordered),
        median=statistics.median(ordered),
        p90=ordered[math.ceil(_P90 * len(ordered)) - 1],
    )


def _summaries(results: list[RunResult]) -> list[RoundSummary]:
    """Average each Round over every run, holding a finished run at its end."""
    length = max(len(result.snapshots) for result in results)
    summaries = []
    for index in range(length):
        snapshots: list[Snapshot] = [
            result.snapshots[min(index, len(result.snapshots) - 1)]
            for result in results
        ]
        tokens: Counter[str] = Counter()
        for snapshot in snapshots:
            tokens.update(snapshot.tokens)
        runs = len(results)
        summaries.append(
            RoundSummary(
                round=index,
                models=sum(snapshot.models for snapshot in snapshots) / runs,
                future=sum(snapshot.future for snapshot in snapshots) / runs,
                future_crew=sum(snapshot.future_crew for snapshot in snapshots) / runs,
                tokens={name: count / runs for name, count in sorted(tokens.items())},
            )
        )
    return summaries


def _rounds(results: list[RunResult]) -> dict[EndedBy, dict[int, int]]:
    """Count runs by how they ended and after how many Rounds."""
    rounds: dict[EndedBy, Counter[int]] = {}
    for result in results:
        rounds.setdefault(result.ended_by, Counter())[result.rounds] += 1
    return {
        ended_by: dict(sorted(counts.items())) for ended_by, counts in rounds.items()
    }


def _entry_first(
    counts: Counter[DamageTableName], entry: DamageTableName
) -> dict[DamageTableName, int]:
    """Order per-table counts with the entry table first, then by name."""
    return dict(sorted(counts.items(), key=lambda item: (item[0] != entry, item[0])))


def simulate(
    scenario: Scenario,
    *,
    runs: int,
    seed: int | None,
    entry: DamageTableName = "Regular",
) -> DamageReport:
    """Run a Scenario `runs` times from one seed, choosing a seed if none is given."""
    seed = secrets.randbelow(_SEED_BOUND) if seed is None else seed
    roller = RandomRoller.seeded(seed)
    results = [run_once(scenario, roller) for _ in range(runs)]
    table_rolls: Counter[DamageTableName] = Counter()
    missing: Counter[DamageTableName] = Counter()
    spillover: Counter[str] = Counter()
    unparsed: Counter[tuple[DamageTableName, str, str]] = Counter()
    for result in results:
        table_rolls.update(result.table_rolls)
        missing.update(result.missing_tables)
        spillover.update(result.spillover)
        unparsed.update(result.unparsed)
    return DamageReport(
        unit=scenario.unit,
        entry=entry,
        runs=runs,
        seed=seed,
        p_destroyed=sum(result.destroyed for result in results) / runs,
        points=scenario.points,
        models_lost=_spread([result.models_lost for result in results]),
        rounds=_rounds(results),
        ended_by=dict(Counter(result.ended_by for result in results)),
        per_round=_summaries(results),
        table_rolls=_entry_first(table_rolls, entry),
        missing_tables=_entry_first(missing, entry),
        spillover=dict(spillover.most_common()),
        unparsed=[
            UnparsedHit(table=table, row=row, text=text, hits=hits)
            for (table, row, text), hits in sorted(
                unparsed.items(),
                key=lambda item: (item[0][0] != entry, item[0][0], -item[1]),
            )
        ],
    )
