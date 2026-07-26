"""Rules commands for the SteamPunkFantasy CLI."""

import cyclopts

from spf import rules
from spf.config import config
from spf.console import stderr, stdout
from spf.render.rulebook import build_rulebook


def add_commands(app: cyclopts.App) -> None:
    """Add race commands to the CLI."""
    app.command(list_special_rules, name="specials")
    app.command(list_token_rules, name="tokens")
    app.command(list_hex_rules, name="hexes")
    app.command(list_rulebook, name="rulebook")


def list_special_rules() -> None:
    """Validate and list special rules."""
    stdout.print(rules.get_specials())


def list_token_rules() -> None:
    """Validate and list token rules."""
    stdout.print(rules.get_tokens())


def list_hex_rules() -> None:
    """Validate and list hex rules."""
    stdout.print(rules.get_hexes())


def list_rulebook() -> None:
    """Validate the Rulebook Index and list its sections.

    Resolving the Index is what validates it: every Kind is looked up and every
    source located. That is why this sits in `just validate` — a broken Index
    should fail `just check`, not the next person's `spf render general-rules`.
    """
    try:
        rulebook = build_rulebook(rules.get_rulebook(), rules_dir=config.paths.rules)
    except (FileNotFoundError, ValueError) as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    stdout.print(rulebook.title)
    for position, section in enumerate(rulebook.sections, start=1):
        # Parentheses, not brackets: Rich would read `[markdown]` as a style tag
        # and swallow it.
        stdout.print(f"{position}. {section.title} ({section.kind})")
