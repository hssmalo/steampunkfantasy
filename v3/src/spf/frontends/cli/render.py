"""Render commands for the SteamPunkFantasy CLI.

Registers the ``spf render`` group and its product subcommands, plus the reusable
``RenderOpts`` parameter set they accept.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import cyclopts

from spf.armies import io
from spf.console import stderr, stdout
from spf.render import Product, render
from spf.render.cards import build_deck
from spf.render.formats import FORMATS, get_format
from spf.render.products import register_product

DEFAULT_FORMAT = "pdf"

# The Order Card Product: templates live at ``<family>/cards/main.<ext>.jinja``.
CARDS = register_product(Product(name="cards"))


def _validate_format(_type: type, value: str) -> None:
    """Reject a ``--format`` value not registered in the Format registry."""
    if value not in FORMATS:
        known = ", ".join(FORMATS)
        msg = f"Unknown format {value!r}; choose from: {known}"
        raise ValueError(msg)


@dataclass
class RenderOpts:
    """Reusable options for render subcommands."""

    format: Annotated[
        str,
        cyclopts.Parameter(
            validator=_validate_format,
            help="Output format (one of the registered Formats).",
        ),
    ] = DEFAULT_FORMAT
    out: Annotated[
        Path | None,
        cyclopts.Parameter(help="Explicit output path, overriding the default layout."),
    ] = None


def _safe_stem(name: str) -> str:
    """Slugify ``name`` to a filename stem of letters, digits, and single dashes."""
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-")


def render_cards(
    army_name: str,
    *,
    opts: Annotated[RenderOpts | None, cyclopts.Parameter(name="*")] = None,
) -> None:
    """Render an army's order cards to a deck file."""
    opts = opts or RenderOpts()
    try:
        army = io.load_army(army_name)
    except (FileNotFoundError, ValueError) as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    stem = _safe_stem(army_name)
    deck = build_deck(army, stem=stem)
    fmt = get_format(opts.format)
    out = render(CARDS, deck, fmt, name=stem, out=opts.out)
    stdout.print(f"Wrote {out}")


def add_commands(app: cyclopts.App) -> None:
    """Add render commands to the CLI."""
    app.command(render_cards, name="cards")
