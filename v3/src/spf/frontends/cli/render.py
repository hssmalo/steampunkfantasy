"""Render commands for the SteamPunkFantasy CLI.

Registers the `spf render` group and its product subcommands, plus the reusable
`RenderOpts` parameter set they accept.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import cyclopts

from spf.armies import io
from spf.console import stderr, stdout
from spf.render import Product, render
from spf.render.army_rules import build_reference
from spf.render.cards import build_deck
from spf.render.formats import FORMATS, get_format
from spf.render.images import committed_image, no_image
from spf.render.products import register_product
from spf.render.rulebook import build_rulebook
from spf.rules import get_rulebook, rulebook_index_path

DEFAULT_FORMAT = "pdf"

# The Rulebook always renders to one file under this stem: unlike the Army
# products it has no per-army name to derive one from.
RULEBOOK_STEM = "rulebook"

# The Order Card Product: templates live at `<family>/cards/main.<ext>.jinja`.
CARDS = register_product(Product(name="cards"))

# The Army Reference Product: templates live at
# `<family>/army-rules/main.<ext>.jinja`.
ARMY_RULES = register_product(Product(name="army-rules"))

# The Rulebook Product: templates live at
# `<family>/general-rules/main.<ext>.jinja`, plus one partial per Section Kind.
GENERAL_RULES = register_product(Product(name="general-rules"))


def _validate_format(_type: type, value: str) -> None:
    """Reject a `--format` value not registered in the Format registry."""
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
    no_images: Annotated[
        bool,
        cyclopts.Parameter(
            # The auto-derived negative would read `--no-no-images`.
            negative="",
            help="Leave committed Image Assets out of the document.",
        ),
    ] = False


def _safe_stem(name: str) -> str:
    """Slugify `name` to a filename stem of letters, digits, and single dashes."""
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
    deck = build_deck(
        army, stem=stem, image_for=no_image if opts.no_images else committed_image
    )
    fmt = get_format(opts.format)
    out = render(CARDS, deck, fmt=fmt, name=stem, out=opts.out)
    stdout.print(f"Wrote {out}")


def render_army_rules(
    army_name: str,
    *,
    opts: Annotated[RenderOpts | None, cyclopts.Parameter(name="*")] = None,
) -> None:
    """Render an army's rules reference to a document."""
    opts = opts or RenderOpts()
    try:
        army = io.load_army(army_name)
    except (FileNotFoundError, ValueError) as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    stem = _safe_stem(army_name)
    reference = build_reference(
        army, stem=stem, image_for=no_image if opts.no_images else committed_image
    )
    fmt = get_format(opts.format)
    out = render(ARMY_RULES, reference, fmt=fmt, name=stem, out=opts.out)
    stdout.print(f"Wrote {out}")


def render_general_rules(
    *,
    index: Annotated[
        Path | None,
        cyclopts.Parameter(help="Alternate Rulebook Index; sources resolve beside it."),
    ] = None,
    opts: Annotated[RenderOpts | None, cyclopts.Parameter(name="*")] = None,
) -> None:
    """Render the general, army-agnostic rules to a rulebook."""
    opts = opts or RenderOpts()
    index_path = rulebook_index_path(index)
    try:
        # Sources resolve beside the Index rather than in `rules/` always, so an
        # alternate Index is self-contained — and for the committed one the two
        # are the same directory.
        rulebook = build_rulebook(get_rulebook(index_path), rules_dir=index_path.parent)
    except (FileNotFoundError, ValueError) as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    fmt = get_format(opts.format)
    out = render(GENERAL_RULES, rulebook, fmt=fmt, name=RULEBOOK_STEM, out=opts.out)
    stdout.print(f"Wrote {out}")


def add_commands(app: cyclopts.App) -> None:
    """Add render commands to the CLI."""
    app.command(render_cards, name="cards")
    app.command(render_army_rules, name="army-rules")
    app.command(render_general_rules, name="general-rules")
