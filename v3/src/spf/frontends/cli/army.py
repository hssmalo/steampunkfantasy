"""Army commands for the SteamPunkFantasy CLI."""

import pathlib

import cyclopts

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
        army = io.load_army(army_name, tournament=tournament, validate=False)

        stdout.print(
            f"- {army_id:<24} {army.race.title():<16} {army.nick:<32}",
            highlight=False,
        )


def show_army(army_name: str) -> None:
    """Load and display a saved army."""
    try:
        army = io.load_army(army_name)
    except (FileNotFoundError, ValueError) as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    io.print_army(army)


def _parse_army_path(
    army_path: pathlib.Path,
) -> tuple[str, str, str]:
    """Parse an army path into army_id, tournament, and army_name."""
    army_id = str(army_path.relative_to(config.paths.armies).with_suffix(""))
    tournament, _, army_name = army_id.rpartition("/")
    return army_id, tournament, army_name
