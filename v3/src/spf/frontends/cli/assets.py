"""Asset commands for the SteamPunkFantasy CLI.

Ships the shared, kind-agnostic ``spf assets promote`` command, the reusable
``AssetOpts`` parameter set that per-kind ``generate`` subcommands accept, and
the first concrete generate subcommand, ``spf assets image``.
"""

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, cast

import cyclopts

from spf import races
from spf.assets import generate, get_kind, promote
from spf.assets import image as _image  # noqa: F401  registers the "image" Kind
from spf.assets.comfyui import ComfyUIError
from spf.config import config
from spf.console import stderr, stdout

if TYPE_CHECKING:
    from spf.schemas import type_aliases as t

_SEED_BOUND = 2**31


def _validate_kind(_type: type, value: str) -> None:
    """Reject a KIND that is not registered, surfacing the known kinds."""
    get_kind(value)  # raises ValueError naming the known kinds


Kind = Annotated[str, cyclopts.Parameter(validator=_validate_kind)]


@dataclass
class AssetOpts:
    """Reusable options for asset generate subcommands."""

    count: int | None = None
    seed: int | None = None


def _resolve_target(race: str, unit: str | None) -> tuple[str, str, str]:
    """Return ``(name, human_name, description)`` for a race or unit target.

    ``race`` must be a known race; ``unit`` (when given) a known unit key of it.
    Raises :class:`ValueError` mirroring ``get_race`` for unknown names.
    """
    race_name = cast("t.RaceName", race)
    if unit is None:
        metadata = races.get_metadata(race_name)  # raises ValueError for unknown race
        return race, metadata.name, metadata.description
    units = races.get_units(race_name)  # raises ValueError for unknown race
    try:
        config_unit = units[unit]
    except KeyError:
        available = ", ".join(units)
        msg = f"Unknown unit '{unit}' for race '{race}'. Available units: {available}"
        raise ValueError(msg) from None
    return unit, config_unit.name, config_unit.description


def add_commands(app: cyclopts.App) -> None:
    """Add asset commands to the CLI."""

    def promote_asset(race: str, kind: Kind, name: str, *, pick: int) -> None:
        """Promote the picked Candidate into the committed Asset store.

        RACE is the race the Asset belongs to, KIND its Asset kind, NAME its base
        file name. ``--pick`` selects the 1-based Candidate to commit.
        """
        promote(
            get_kind(kind),
            race=race,
            name=name,
            pick=pick,
            candidates_root=config.paths.candidates,
            assets_root=config.paths.assets,
        )

    def image(
        race: str,
        unit: str | None = None,
        *,
        opts: Annotated[AssetOpts | None, cyclopts.Parameter(name="*")] = None,
    ) -> None:
        """Generate image Candidates for a RACE, or a UNIT of it.

        The prompt is composed from ``prompts/image.txt`` plus the target's name
        and description; a target without a description is a hard error.
        """
        opts = opts or AssetOpts()
        try:
            name, human_name, description = _resolve_target(race, unit)
        except ValueError as err:
            stderr.print(f"[red]Error:[/] {err}")
            raise SystemExit(1) from None

        target = unit or race
        if not description.strip():
            stderr.print(
                f"[red]Error:[/] no description for {target!r}, "
                "cannot generate an image"
            )
            raise SystemExit(1)

        preamble = " ".join(
            (config.paths.prompts / "image.txt").read_text(encoding="utf-8").split()
        )
        prompt = f"{preamble} {human_name}. {description}"

        seed = (
            opts.seed if opts.seed is not None else random.randrange(_SEED_BOUND)  # noqa: S311  seed, not cryptographic
        )
        stdout.print(f"Seed: {seed}  (rerun with --seed {seed} to reproduce)")
        count = opts.count or config.assets.image.count

        # Show the composed prompt (dimmed) before sending it to the Service.
        stdout.print(prompt, style="dim", markup=False)

        try:
            generate(
                get_kind("image"),
                prompt,
                race=race,
                name=name,
                count=count,
                seed=seed,
                candidates_root=config.paths.candidates,
                on_candidate=lambda path: stdout.print(f"Wrote {path}"),
            )
        except (OSError, ComfyUIError) as err:
            stderr.print(f"[red]Error:[/] image generation failed: {err}")
            raise SystemExit(1) from None

        stdout.print(
            f"Promote one with: spf assets promote {race} image {target} --pick N"
        )

    app.command(promote_asset, name="promote")
    app.command(image, name="image")
