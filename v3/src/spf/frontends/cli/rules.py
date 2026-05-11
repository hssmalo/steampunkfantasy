"""Rules commands for the SteamPunkFantasy CLI."""

import cyclopts

from spf import rules
from spf.console import stdout


def add_commands(app: cyclopts.App) -> None:
    """Add race commands to the CLI."""
    app.command(list_special_rules, name="specials")
    app.command(list_token_rules, name="tokens")
    app.command(list_hex_rules, name="hexes")


def list_special_rules() -> None:
    """Validate and list special rules."""
    stdout.print(rules.get_specials())


def list_token_rules() -> None:
    """Validate and list token rules."""
    stdout.print(rules.get_tokens())


def list_hex_rules() -> None:
    """Validate and list hex rules."""
    stdout.print(rules.get_hexes())
