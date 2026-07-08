"""Render commands for the SteamPunkFantasy CLI.

This foundation registers the empty ``spf render`` group and provides the
reusable ``RenderOpts`` parameter set that product subcommands will accept. No
product subcommand is added here — those land in the product issues.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import cyclopts

from spf.render.formats import FORMATS

DEFAULT_FORMAT = "pdf"


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


def add_commands(app: cyclopts.App) -> None:
    """Add render commands to the CLI.

    No product subcommands exist in the foundation; each product issue registers
    its own here.
    """
