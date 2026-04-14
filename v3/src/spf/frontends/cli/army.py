"""Army commands for the SteamPunkFantasy CLI."""

import pathlib

import cyclopts

from spf import races
from spf.armies import io
from spf.config import config
from spf.console import stderr, stdout


def add_commands(app: cyclopts.App) -> None:
    """Add army commands to the CLI."""
    app.command(list_armies, name="list")
    app.command(show_army, name="show")


def list_armies() -> None:
    """List available armies."""
    for army_path in io.list_armies():
        army_id, tournament, army_name = _parse_army_path(army_path)
        army = io.load_army(army_name, tournament=tournament)

        stdout.print(
            (
                f"- {army_id:<24} {army.race.title():<16}"
                f" [dim]{army_path.relative_to(config.paths.project)}[/]"
            ),
            highlight=False,
        )


def show_army(army_name: str) -> None:
    """Load and display a saved army."""
    try:
        army = io.load_army(army_name)
    except (FileNotFoundError, ValueError) as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    cfg = races.get_race(army.race)
    io.print_army(army, cfg)


def _parse_army_path(
    army_path: pathlib.Path,
) -> tuple[str, str, str]:
    """Parse an army path into army_id, tournament, and army_name."""
    army_id = str(army_path.relative_to(config.paths.armies).with_suffix(""))
    tournament, _, army_name = army_id.rpartition("/")
    return army_id, tournament, army_name
