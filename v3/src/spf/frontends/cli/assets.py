"""Asset commands for the SteamPunkFantasy CLI.

Ships the shared, kind-agnostic `spf assets promote` and `spf assets refine`
commands, the reusable `AssetOpts` parameter set that per-kind `generate`
subcommands accept, and the first concrete generate subcommand,
`spf assets image`.
"""

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import cyclopts

from spf import races
from spf.assets import generate, get_kind, promote, refine, validate_lineage
from spf.assets import image as _image  # noqa: F401  registers the "image" Kind
from spf.assets.comfyui import ComfyUIError
from spf.config import config
from spf.console import stderr, stdout
from spf.schemas import type_aliases as t

_SEED_BOUND = 2**31


def add_commands(app: cyclopts.App) -> None:
    """Add asset commands to the CLI."""
    app.command(promote_asset, name="promote")
    app.command(refine_asset, name="refine")
    app.command(image, name="image")


def _validate_kind(_type: type, value: str) -> None:
    """Reject a KIND that is not registered, surfacing the known kinds."""
    get_kind(value)  # raises ValueError naming the known kinds


Kind = Annotated[str, cyclopts.Parameter(validator=_validate_kind)]


def _negative_prompt_path() -> Path:
    """Where the Image Service reads its Negative Prompt from (issue 50, D7).

    Echoed by path, not by content: unlike the composed positive prompt it is
    static and version-controlled, so naming the file keeps it discoverable
    without scrolling the varying prompt off screen.
    """
    return config.paths.prompts / "image-negative.txt"


def _validate_lineage(_type: type, value: str) -> None:
    """Reject a Lineage that is not a dotted 1-based index."""
    validate_lineage(value)  # raises ValueError describing the expected shape


Lineage = Annotated[str, cyclopts.Parameter(validator=_validate_lineage)]


@dataclass
class AssetOpts:
    """Reusable options for asset generate subcommands."""

    count: int | None = None
    seed: int | None = None

    def resolve(self) -> tuple[int, int]:
        """Return the `(count, seed)` to run with, filling in the defaults.

        An unset `--seed` draws a fresh one so the run is still reproducible
        after the fact: the caller prints it back for `--seed N`.
        """
        seed = self.seed if self.seed is not None else random.randrange(_SEED_BOUND)  # noqa: S311  seed, not cryptographic
        return self.count or config.assets.image.count, seed


def _resolve_target(race: t.RaceName, unit: str | None) -> tuple[str, str, str]:
    """Return `(name, human_name, description)` for a race or unit target.

    `race` must be a known race; `unit` (when given) a known unit key of it.
    Raises `ValueError` mirroring `get_race` for unknown names.
    """
    if unit is None:
        metadata = races.get_metadata(race)  # raises ValueError for unknown race
        return race, metadata.name, metadata.description
    units = races.get_units(race)  # raises ValueError for unknown race
    try:
        config_unit = units[unit]
    except KeyError:
        available = ", ".join(units)
        msg = f"Unknown unit '{unit}' for race '{race}'. Available units: {available}"
        raise ValueError(msg) from None
    return unit, config_unit.name, config_unit.description


def promote_asset(race: t.RaceName, kind: Kind, name: str, *, pick: Lineage) -> None:
    """Promote the picked Candidate into the committed Asset store.

    RACE is the race the Asset belongs to, KIND its Asset kind, NAME its base
    file name. `--pick` selects the Candidate to commit by Lineage — a dotted
    1-based index, so `2` picks an original and `2.1` a Refinement of it.
    """
    promote(
        get_kind(kind),
        race=race,
        name=name,
        pick=pick,
        candidates_root=config.paths.candidates,
        assets_root=config.paths.assets,
    )


def refine_asset(  # noqa: PLR0913  mirrors promote, plus the Correction and opts
    race: t.RaceName,
    kind: Kind,
    name: str,
    correction: str,
    *,
    from_: Annotated[Lineage, cyclopts.Parameter(name="--from")],
    opts: Annotated[AssetOpts | None, cyclopts.Parameter(name="*")] = None,
) -> None:
    """Refine an existing Candidate by applying a CORRECTION to it.

    RACE is the race the Asset belongs to, KIND its Asset kind, NAME its base
    file name, and CORRECTION the edit to apply ("make the hat brass instead
    of leather"). `--from` picks the Candidate to refine by Lineage, the same
    dotted index `promote --pick` takes.

    The Correction is the whole prompt — no `prompts/image.txt` preamble and no
    race description, because an instruction-edit model is trained on
    instructions. Results land under the derived name `NAME.LINEAGE`, so
    refining `2` writes `2.1`, `2.2`, … and the original is left alone.
    """
    count, seed = (opts or AssetOpts()).resolve()
    stdout.print(f"Seed: {seed}  (rerun with --seed {seed} to reproduce)")

    # Show what is actually sent (dimmed), matching `image`; here it is just
    # the Correction. The Negative Prompt is an image concern, so name its file
    # only when an image is what is being refined.
    stdout.print(correction, style="dim", markup=False)
    if kind == "image":
        stdout.print(
            f"Negative: {_negative_prompt_path()}", style="dim", soft_wrap=True
        )

    try:
        refine(
            get_kind(kind),
            correction,
            race=race,
            name=name,
            lineage=from_,
            count=count,
            seed=seed,
            candidates_root=config.paths.candidates,
            on_candidate=lambda path: stdout.print(f"Wrote {path}"),
        )
    except (OSError, ComfyUIError, TypeError, ValueError) as err:
        stderr.print(f"[red]Error:[/] refinement failed: {err}")
        raise SystemExit(1) from None

    stdout.print(
        f"Promote one with: spf assets promote {race} {kind} {name} --pick {from_}.N"
    )


def image(
    race: t.RaceName,
    unit: str | None = None,
    *,
    opts: Annotated[AssetOpts | None, cyclopts.Parameter(name="*")] = None,
) -> None:
    """Generate image Candidates for a RACE, or a UNIT of it.

    The prompt is composed from `prompts/image.txt` plus the target's name
    and description; a target without a description is a hard error.
    """
    opts = opts or AssetOpts()

    if unit == "all":
        for unit_name in [None, *races.get_units(race)]:
            if unit_name:
                stdout.print(f"[green]{unit_name}[/]")
            image(race, unit=unit_name, opts=opts)
        return

    try:
        name, human_name, description = _resolve_target(race, unit)
    except ValueError as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    target = unit or race
    if not description.strip():
        stderr.print(
            f"[red]Error:[/] no description for {target!r}, cannot generate an image"
        )
        raise SystemExit(1)

    system = (config.paths.prompts / "image.txt").read_text(encoding="utf-8")
    prompt = f"Subject: {human_name}.\nDetails: {description}\n{system}"

    count, seed = opts.resolve()
    stdout.print(f"Seed: {seed}  (rerun with --seed {seed} to reproduce)")

    # Show the composed prompt (dimmed) before sending it to the Service.
    stdout.print(prompt, style="dim", markup=False)
    stdout.print(f"Negative: {_negative_prompt_path()}", style="dim", soft_wrap=True)

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

    stdout.print(f"Promote one with: spf assets promote {race} image {target} --pick N")
