"""Simulator commands for the SteamPunkFantasy CLI."""

import re
from collections.abc import Iterable
from typing import Annotated, cast

import cyclopts
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from spf import races
from spf.console import stdout
from spf.frontends.cli.suggest import resolve_or_raise
from spf.prose import plain
from spf.registry import load_registry
from spf.schemas import type_aliases as t
from spf.schemas.race import RaceConfig
from spf.sim.report import DamageReport, RoundSummary, simulate
from spf.sim.scenario import GRAMMAR, Scenario, parse_hits, parse_start
from spf.sim.tables import CompiledTable
from spf.sim.units import unit_scenario

_START_HELP = f"The starting state. {GRAMMAR}"
_STRENGTH = re.compile(r"(?P<name>.+)\[(?P<strength>\d+)\]")
UNPARSED_STYLE = "bold red"
"""How Damage table text the simulator does not play is colored."""
NO_POINTS = "\N{EN DASH}"
"""How a Unit with no Cost shows its Points and E(Points Destroyed)."""


def add_commands(app: cyclopts.App) -> None:
    """Add simulator commands to the CLI."""
    app.command(damage, name="damage")
    app.command(damage_race, name="damage-race")


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
    race = _race(race_name)
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
    print_tables(scenario, entry=table)
    print_report(simulate(scenario, runs=runs, seed=seed, entry=table))


def damage_race(  # noqa: PLR0913
    race_name: str,
    *,
    table: t.DamageTableName = "Regular",
    start: Annotated[str, cyclopts.Parameter(help=_START_HELP)] = "",
    incoming: str = "",
    runs: int = 10_000,
    seed: int | None = None,
    max_rounds: int = 20,
    resistance: bool = True,
) -> None:
    """Simulate the same damage on every Unit of a Race, one line per Unit.

    Every Unit uses the same seed, so `spf sim damage race.unit --seed N`
    reproduces any line in full.

    Parameters
    ----------
    race_name
        The Race: `dwarf`.
    table
        The Damage table bare rolls land on. Units without it are skipped.
    start
        The starting state; the full grammar is in `--help`.
    incoming
        Rolls landing every Round, written as for --start.
    runs
        How many runs to simulate per Unit.
    seed
        Seed for the dice. A seed is chosen and printed when none is given.
    max_rounds
        The most Rounds one run plays.
    resistance
        Apply the Units' resistances. Turn off to compare.

    """
    race = _race(race_name)
    registry = load_registry()
    hits, rolling = parse_start(start, table=table), parse_hits(incoming, table=table)
    reports: list[DamageReport] = []
    skipped: list[str] = []
    for unit_key, config in race.units.items():
        if table not in config.damage_tables:
            skipped.append(config.name)
            continue
        scenario = unit_scenario(
            race,
            unit_key,
            registry=registry,
            start=hits,
            incoming=rolling,
            max_rounds=max_rounds,
            resistance=resistance,
        )
        reports.append(simulate(scenario, runs=runs, seed=seed, entry=table))
        seed = reports[-1].seed
    print_race_report(reports, race=race_name)
    if skipped:
        stdout.print(f"No {table} damage table, skipped: {escape(', '.join(skipped))}")


def _race(name: str) -> RaceConfig:
    """Look up a Race by name, suggesting a close match when it is unknown."""
    name = resolve_or_raise(name, races.list_races(), noun="race", see="spf race list")
    return races.get_race(cast("t.RaceName", name))


def print_race_report(reports: list[DamageReport], *, race: str) -> None:
    """Print one line per Unit: its odds, its losses and its state at the end."""
    if not reports:
        return
    _print_heading(reports[0], title=race)
    stdout.print(_unit_lines(reports))


def print_army_report(
    reports: list[DamageReport], *, title: str, positions: list[int]
) -> None:
    """Print one line per Army Unit, numbered by its position, then a Total row.

    The Total sums the Points and E(Points Destroyed) of the Units with a Cost:
    what an opponent expects to score if every Unit took this damage separately.
    """
    if not reports:
        return
    _print_heading(reports[0], title=title)
    lines = _unit_lines(reports, positions=positions)
    costed = [report for report in reports if report.points is not None]
    points = sum(report.points or 0 for report in costed)
    expected = sum(report.expected_points_destroyed or 0.0 for report in costed)
    total = ["", "Total", points_text(points if costed else None), ""]
    total.append(expected_points_text(expected if costed else None))
    lines.add_section()
    lines.add_row(*total, *[""] * (len(lines.columns) - len(total)))
    stdout.print(lines)


def _print_heading(first: DamageReport, *, title: str) -> None:
    """Print the line naming what was simulated, and how."""
    stdout.print(
        f"[bold]{escape(title)}[/] — {first.runs} runs per Unit, seed {first.seed},"
        f" entry table {first.entry}",
        highlight=False,
    )


def _unit_lines(
    reports: list[DamageReport], *, positions: list[int] | None = None
) -> Table:
    """Build the table of one line per Unit, numbered when `positions` is given."""
    finals = [report.per_round[-1] for report in reports]
    tokens = token_columns(finals)
    lines = Table(
        *(["#"] if positions is not None else []),
        "Unit",
        "Points",
        "P(Destroyed)",
        "E(Points Destroyed)",
        "Models lost",
        "Round",
        "Models",
        "Future",
        "Future Crew",
        *tokens,
        title="Mean state at the end of the last Round",
        title_justify="left",
    )
    numbers = [[str(n)] for n in positions] if positions is not None else None
    for i, (report, final) in enumerate(zip(reports, finals, strict=True)):
        lines.add_row(
            *(numbers[i] if numbers is not None else []),
            escape(report.unit),
            points_text(report.points),
            f"{report.p_destroyed:.1%}",
            expected_points_text(report.expected_points_destroyed),
            f"{report.models_lost.mean:.2f}",
            str(final.round),
            f"{final.models:.2f}",
            f"{final.future:.2f}",
            f"{final.future_crew:.2f}",
            *(f"{final.tokens.get(name, 0.0):.2f}" for name in tokens),
        )
    return lines


def print_tables(scenario: Scenario, *, entry: t.DamageTableName) -> None:
    """Print the Unit's Damage tables, the entry table first."""
    tables = sorted(scenario.tables.values(), key=lambda table: table.name != entry)
    for table in tables:
        stdout.print(damage_table(table))
    if any(_has_unparsed(table) for table in tables):
        stdout.print(Text("Colored text is not simulated.", style=UNPARSED_STYLE))


def _has_unparsed(table: CompiledTable) -> bool:
    """Tell whether any of a table's rows or notes holds text not simulated."""
    return bool(table.notes.unparsed) or any(
        not segment.simulated for row in table.rows for segment in row.segments()
    )


def damage_table(table: CompiledTable) -> Table:
    """Render one Damage table, coloring the text the simulator does not play."""
    rendered = Table(
        "Roll",
        "Effect",
        title=f"{table.name} damage table",
        title_justify="left",
        caption_justify="left",
    )
    for row in table.rows:
        effect = Text()
        for segment in row.segments():
            effect.append(
                segment.text, style=None if segment.simulated else UNPARSED_STYLE
            )
        rendered.add_row(row.label, effect)
    if table.written_notes:
        rendered.caption = Text("\n").join(
            Text(
                plain(note),
                style=UNPARSED_STYLE if note in table.notes.unparsed else "",
            )
            for note in table.written_notes
        )
    return rendered


def print_report(report: DamageReport) -> None:
    """Print a DamageReport as Rich tables."""
    stdout.print(
        f"[bold]{escape(report.unit)}[/] — {report.runs} runs, seed {report.seed},"
        f" entry table {report.entry}",
        highlight=False,
    )
    lost = report.models_lost
    summary = Table("Outcome", "Value", title="Summary", title_justify="left")
    summary.add_row("P(Destroyed)", f"{report.p_destroyed:.1%}")
    summary.add_row("Points", points_text(report.points))
    summary.add_row(
        "E(Points Destroyed)", expected_points_text(report.expected_points_destroyed)
    )
    summary.add_row(
        "Models lost", f"mean {lost.mean:.2f}, median {lost.median:g}, p90 {lost.p90:g}"
    )
    for ended_by, count in report.ended_by.items():
        summary.add_row(f"Ended: {ended_by}", f"{count / report.runs:.1%}")
    stdout.print(summary)

    endings = list(report.rounds)
    rounds = Table(
        "Rounds",
        *(f"Ended: {ending}" for ending in endings),
        title="Rounds played, by how the run ended",
        title_justify="left",
    )
    for played in sorted({n for by_round in report.rounds.values() for n in by_round}):
        rounds.add_row(
            str(played),
            *(
                f"{report.rounds[ending].get(played, 0) / report.runs:.1%}"
                for ending in endings
            ),
        )
    stdout.print(rounds)

    tokens = token_columns(report.per_round)
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


def points_text(points: int | None) -> str:
    """Show a Unit's Points, or `NO_POINTS` when it has no Cost."""
    return NO_POINTS if points is None else str(points)


def expected_points_text(value: float | None) -> str:
    """Show E(Points Destroyed), or `NO_POINTS` when the Unit has no Cost."""
    return NO_POINTS if value is None else f"{value:.2f}"


def token_columns(per_round: Iterable[RoundSummary]) -> list[str]:
    """List every Token any Round holds, a token's strengths smallest first."""
    names = {name for summary in per_round for name in summary.tokens}
    return sorted(names, key=_by_strength)


def _by_strength(name: str) -> tuple[str, int]:
    """Sort `bleed[10]` after `bleed[4]`: by name, then by numeric strength."""
    if match := _STRENGTH.fullmatch(name):
        return match["name"], int(match["strength"])
    return name, 0


def _counts(title: str, label: str, counts: Iterable[tuple[str, int]]) -> None:
    """Print one count per name, if there are any."""
    if not (rows := list(counts)):
        return
    table = Table(label, "Count", title=title, title_justify="left")
    for name, count in rows:
        table.add_row(escape(name), str(count))
    stdout.print(table)
