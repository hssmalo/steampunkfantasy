"""Simulator commands for the SteamPunkFantasy CLI."""

from collections.abc import Iterable
from typing import Annotated, cast

import cyclopts
from rich.markup import escape
from rich.table import Table

from spf import races
from spf.console import stdout
from spf.frontends.cli.suggest import resolve_or_raise
from spf.registry import load_registry
from spf.schemas import type_aliases as t
from spf.sim.report import DamageReport, simulate
from spf.sim.scenario import GRAMMAR, parse_hits, parse_start
from spf.sim.units import unit_scenario

_START_HELP = f"The starting state. {GRAMMAR}"


def add_commands(app: cyclopts.App) -> None:
    """Add simulator commands to the CLI."""
    app.command(damage, name="damage")


def damage(  # noqa: PLR0913
    unit: str,
    *,
    table: t.DamageTableName = "Regular",
    start: Annotated[str, cyclopts.Parameter(help=_START_HELP)] = "",
    incoming: str = "",
    runs: int = 10_000,
    seed: int | None = None,
    max_rounds: int = 20,
    resistance: bool = True,
) -> None:
    """Simulate how damage plays out on one Unit over time.

    Parameters
    ----------
    unit
        The Unit, as `race.unit`: `dwarf.dwarf_infantry`.
    table
        The Damage table bare rolls land on; its figures are reported first.
    start
        The starting state; the full grammar is in `--help`.
    incoming
        Rolls landing every Round, written as for --start.
    runs
        How many runs to simulate.
    seed
        Seed for the dice. A seed is chosen and printed when none is given.
    max_rounds
        The most Rounds one run plays.
    resistance
        Apply the Unit's resistances. Turn off to compare.

    """
    race_name, _, unit_key = unit.partition(".")
    race_name = resolve_or_raise(
        race_name, races.list_races(), noun="race", see="spf race list"
    )
    race = races.get_race(cast("t.RaceName", race_name))
    unit_key = resolve_or_raise(
        unit_key, race.units, noun="unit", see=f"spf race units {race_name}"
    )
    scenario = unit_scenario(
        race,
        unit_key,
        registry=load_registry(),
        start=parse_start(start, table=table),
        incoming=parse_hits(incoming, table=table),
        max_rounds=max_rounds,
        resistance=resistance,
    )
    print_report(simulate(scenario, runs=runs, seed=seed, entry=table))


def print_report(report: DamageReport) -> None:
    """Print a DamageReport as Rich tables."""
    stdout.print(
        f"[bold]{escape(report.unit)}[/] — {report.runs} runs, seed {report.seed},"
        f" entry table {report.entry}",
        highlight=False,
    )
    lost = report.models_lost
    summary = Table("Outcome", "Value", title="Summary", title_justify="left")
    summary.add_row("P(Unit Destroyed)", f"{report.p_destroyed:.1%}")
    summary.add_row(
        "Models lost", f"mean {lost.mean:.2f}, median {lost.median:g}, p90 {lost.p90:g}"
    )
    for ended_by, count in report.ended_by.items():
        summary.add_row(f"Ended: {ended_by}", f"{count / report.runs:.1%}")
    stdout.print(summary)

    rounds = Table("Rounds", "Runs", title="Rounds played", title_justify="left")
    for played, count in report.rounds.items():
        rounds.add_row(str(played), f"{count / report.runs:.1%}")
    stdout.print(rounds)

    tokens = sorted({name for summary in report.per_round for name in summary.tokens})
    per_round = Table(
        "Round",
        "Models",
        "Future",
        "Future Crew",
        *tokens,
        title="Mean state at the end of each Round",
        title_justify="left",
    )
    for summary in report.per_round:
        per_round.add_row(
            str(summary.round),
            f"{summary.models:.2f}",
            f"{summary.future:.2f}",
            f"{summary.future_crew:.2f}",
            *(f"{summary.tokens.get(name, 0.0):.2f}" for name in tokens),
        )
    stdout.print(per_round)

    _counts("Damage table rolls", "Table", report.table_rolls.items())
    _counts("Rolls on a table the Unit lacks", "Table", report.missing_tables.items())
    _counts("Spillover events", "Effect", report.spillover.items())

    if report.unparsed:
        unparsed = Table(
            "Table",
            "Row",
            "Text",
            "Hits",
            title="Not simulated",
            title_justify="left",
        )
        for hit in report.unparsed:
            unparsed.add_row(hit.table, hit.row, escape(hit.text), str(hit.hits))
        stdout.print(unparsed)


def _counts(title: str, label: str, counts: Iterable[tuple[str, int]]) -> None:
    """Print one count per name, if there are any."""
    if not (rows := list(counts)):
        return
    table = Table(label, "Count", title=title, title_justify="left")
    for name, count in rows:
        table.add_row(escape(name), str(count))
    stdout.print(table)
