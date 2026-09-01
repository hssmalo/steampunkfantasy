"""Rules commands for the SteamPunkFantasy CLI."""

import cyclopts

from spf import countdown, races, registry, rules
from spf.config import config
from spf.console import stderr, stdout
from spf.render.rulebook import build_rulebook


def add_commands(app: cyclopts.App) -> None:
    """Add race commands to the CLI."""
    app.command(list_special_rules, name="specials")
    app.command(list_token_rules, name="tokens")
    app.command(list_hex_rules, name="hexes")
    app.command(list_terrain_rules, name="terrain")
    app.command(list_modifier_rules, name="modifiers")
    app.command(list_namespaces, name="namespaces")
    app.command(list_rulebook, name="rulebook")
    app.command(list_todos, name="todos")


def list_special_rules() -> None:
    """Validate and list special rules."""
    stdout.print(rules.get_specials())


def list_token_rules() -> None:
    """Validate and list token rules."""
    stdout.print(rules.get_tokens())


def list_hex_rules() -> None:
    """Validate and list hex rules."""
    stdout.print(rules.get_hexes())


def list_terrain_rules() -> None:
    """Validate and list terrain rules."""
    stdout.print(rules.get_terrain())


def list_modifier_rules() -> None:
    """Validate and list to-hit modifiers."""
    stdout.print(rules.get_modifiers())


def list_namespaces() -> None:
    """Validate and list the namespace registry and the damage types."""
    stdout.print(rules.get_namespaces())


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


def _print_entries(title: str, entries: list[countdown.RuleEntry]) -> None:
    """Print one countdown section, its size in the heading."""
    stdout.print(f"[bold]{title}[/] ({len(entries)})")
    for entry in entries:
        stdout.print(f"- {entry.ref:<40} {entry.name}", highlight=False)
        if entry.todo:
            # First line only: a todo may carry rescued design notes running to
            # a paragraph, and this is a count, not the reading list itself.
            stdout.print(f"    {entry.todo.splitlines()[0]}", highlight=False)


def list_todos() -> None:
    """Count what the rule registries still owe the game designer.

    Three separate countdowns, and deliberately outside `just check`: none of
    them is a gate, and a permanent warning tier rots (ADR 0024).
    """
    loaded = registry.load_registry()
    _print_entries("Unwritten rule text", countdown.unwritten(loaded))
    stdout.print()
    _print_entries("Open questions on written rules", countdown.open_questions(loaded))
    stdout.print()
    used = countdown.used_special_ids(
        races.get_race(name) for name in races.list_races(validate=True)
    )
    _print_entries("Unreachable Specials", countdown.unreachable(loaded, used))
