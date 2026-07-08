"""Asset commands for the SteamPunkFantasy CLI.

This foundation registers the shared, kind-agnostic ``spf assets promote``
command and the reusable ``AssetOpts`` parameter set that per-kind ``generate``
subcommands will accept. Those generate subcommands land in the kind issues.
"""

from dataclasses import dataclass
from typing import Annotated

import cyclopts

from spf.assets import get_kind, promote


def _validate_kind(_type: type, value: str) -> None:
    """Reject a KIND that is not registered, surfacing the known kinds."""
    get_kind(value)  # raises ValueError naming the known kinds


Kind = Annotated[str, cyclopts.Parameter(validator=_validate_kind)]


@dataclass
class AssetOpts:
    """Reusable options for asset generate subcommands."""

    count: int | None = None


def add_commands(app: cyclopts.App) -> None:
    """Add asset commands to the CLI."""

    def promote_asset(race: str, kind: Kind, name: str, *, pick: int) -> None:
        """Promote the picked Candidate into the committed Asset store.

        RACE is the race the Asset belongs to, KIND its Asset kind, NAME its base
        file name. ``--pick`` selects the 1-based Candidate to commit.
        """
        promote(get_kind(kind), race=race, name=name, pick=pick)

    app.command(promote_asset, name="promote")
