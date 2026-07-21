"""Race commands for the SteamPunkFantasy CLI."""

import configaroo
import cyclopts

from spf import lint, races
from spf.config import config
from spf.console import stderr, stdout
from spf.schemas import type_aliases as t
from spf.schemas.race import RaceConfig

_NO_COST = "[gray30] -ip  -mp  -xp  -cp[/]"


def add_commands(app: cyclopts.App) -> None:
    """Add race commands to the CLI."""
    app.command(list_races, name="list")
    app.command(show_race, name="show")
    app.command(list_units, name="units")
    app.command(list_models, name="models")
    app.command(list_equipment, name="equipment")
    app.command(list_things, name="things")
    app.command(lint_race, name="lint")


def list_races() -> None:
    """List available races."""
    for race_name in races.list_races(validate=True):
        race_path = config.paths.races / f"{race_name}.toml"
        race = races.get_race(race_name)

        stdout.print(
            f"- {race_name:<20} {race.races[race_name].name:<16}"
            f" [dim]{race_path.relative_to(config.paths.project)}[/]"
        )


def show_race(race_name: t.RaceName, section: str | None = None) -> None:
    """Load and display a saved race."""
    race = races.get_race(race_name)
    configaroo.print_configuration(race, section=section)


def _cost_str(cost: t.Cost | None) -> str:
    """Return a formatted cost string, or a dash placeholder if cost is None."""
    return str(cost) if cost is not None else _NO_COST


def _print_units(race: RaceConfig) -> None:
    """Print one line per unit with name and cost."""
    for unit in sorted(
        race.units.values(), key=lambda unit: unit.cost.sort_idx if unit.cost else 0
    ):
        stdout.print(f"- {unit.name:<40} {_cost_str(unit.cost)}", highlight=False)


def _print_models(race: RaceConfig) -> None:
    """Print one line per model with name and cost."""
    for model in sorted(
        race.models.values(), key=lambda model: model.cost.sort_idx if model.cost else 0
    ):
        stdout.print(f"- {model.name:<40} {_cost_str(model.cost)}", highlight=False)


def _print_equipment(race: RaceConfig) -> None:
    """Print one line per equipment item with name and cost."""
    for equipment in sorted(
        race.equipment.values(),
        key=lambda equipment: equipment.cost.sort_idx if equipment.cost else 0,
    ):
        stdout.print(
            f"- {equipment.name:<40} {_cost_str(equipment.cost)}", highlight=False
        )


def list_units(race_name: t.RaceName) -> None:
    """List units for a race with name and cost."""
    race = races.get_race(race_name)
    _print_units(race)


def list_models(race_name: t.RaceName) -> None:
    """List models for a race with name and cost."""
    race = races.get_race(race_name)
    _print_models(race)


def list_equipment(race_name: t.RaceName) -> None:
    """List equipment for a race with name and cost."""
    race = races.get_race(race_name)
    _print_equipment(race)


def list_things(race_name: t.RaceName) -> None:
    """List units, models, and equipment for a race with name and cost."""
    race = races.get_race(race_name)
    stdout.print("[bold]Units[/]")
    _print_units(race)
    stdout.print("[bold]Models[/]")
    _print_models(race)
    stdout.print("[bold]Equipment[/]")
    _print_equipment(race)


def lint_race(race_name: t.RaceName | None = None) -> None:
    """Check Race data for name and key inconsistencies.

    Lints every Race that validates when given no argument. Style is a soft
    gate layered on the hard one: a Race that fails schema validation is
    skipped rather than reported, because `just validate` owns that failure
    and would otherwise report it twice (ADR 0016).
    """
    valid = races.list_races(validate=True)
    to_lint: list[t.RaceName]
    if race_name is None:
        to_lint = valid
    elif race_name not in valid:
        stderr.print(f"{race_name}: skipped (does not validate)")
        return
    else:
        to_lint = [race_name]

    findings = [finding for name in to_lint for finding in lint.lint_race(name)]
    for finding in findings:
        location = f"{finding.section}.{finding.key}"
        # Soft-wrapped so a finding is always exactly one line: these are
        # meant to be grepped, and Rich would otherwise fold the long ones at
        # the terminal width, splitting a key away from its rule.
        stdout.print(
            f"races/{finding.race}.toml  {location}  {finding.rule}  {finding.message}",
            highlight=False,
            soft_wrap=True,
        )
    if findings:
        raise SystemExit(1)
