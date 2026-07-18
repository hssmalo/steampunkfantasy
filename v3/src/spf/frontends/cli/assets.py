"""Asset commands for the SteamPunkFantasy CLI.

Ships the shared, kind-agnostic `spf assets promote` and `spf assets refine`
commands, the reusable `AssetOpts` parameter set that per-kind `generate`
subcommands accept, and the first concrete generate subcommand,
`spf assets image`.
"""

import random
from dataclasses import dataclass
from typing import Annotated

import cyclopts

from spf import races
from spf.assets import (
    Coverage,
    Target,
    generate,
    get_kind,
    promote,
    refine,
    survey,
    targets,
    validate_lineage,
)
from spf.assets import image as _image  # noqa: F401  registers the "image" Kind
from spf.assets.comfyui import ComfyUIError
from spf.assets.kinds import KINDS
from spf.assets.kinds import Kind as AssetKind
from spf.config import config
from spf.console import stderr, stdout
from spf.schemas import type_aliases as t

_SEED_BOUND = 2**31


def add_commands(app: cyclopts.App) -> None:
    """Add asset commands to the CLI."""
    app.command(list_assets, name="list")
    app.command(promote_asset, name="promote")
    app.command(refine_asset, name="refine")
    app.command(image, name="image")


def _validate_kind(_type: type, value: str) -> None:
    """Reject a KIND that is not registered, surfacing the known kinds."""
    get_kind(value)  # raises ValueError naming the known kinds


Kind = Annotated[str, cyclopts.Parameter(validator=_validate_kind)]


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


def _resolve_target(kind: AssetKind, race: t.RaceName, unit: str | None) -> Target:
    """Return the Target a command addresses: the race itself, or a unit of it.

    `race` must be a known race; `unit` (when given) a known unit key of it.
    Raises `ValueError` mirroring `get_race` for unknown names.
    """
    found = targets(kind, race)  # raises ValueError for unknown race
    wanted = race if unit is None else unit
    level = "race" if unit is None else "unit"
    for target in found:
        if target.level == level and target.name == wanted:
            return target
    available = ", ".join(t_.name for t_ in found if t_.level == "unit")
    msg = f"Unknown unit '{unit}' for race '{race}'. Available units: {available}"
    raise ValueError(msg)


def _print_coverage(row: Coverage) -> None:
    """Print one Coverage row: key first, human name dimmed, then status."""
    # Pad the *plain* text, then wrap it in markup: padding a marked-up string
    # counts the tag characters and misaligns every column.
    status = "[green]✓[/]      " if row.asset else "[red]missing[/]"
    count = f"{len(row.candidates)} candidates" if row.candidates else ""
    stdout.print(
        f"  - {row.target.name:<24} [dim]{row.target.human_name:<24}[/]"
        f" {status} {count}",
        highlight=False,
        soft_wrap=True,  # a coverage row is scanned or piped, never reflowed
    )


def list_assets(
    race: t.RaceName | None = None,
    *,
    kind: Kind | None = None,
    candidates: bool = False,
) -> None:
    """Report which Targets have Assets, and how many Candidates are waiting.

    RACE restricts the report to one race; omitted, every validating race is
    covered. `--kind` restricts it to one registered Asset kind, and
    `--candidates` expands each row into its Candidate Lineages, marking the
    one the Asset was promoted from.

    Missing Assets are a normal state, so this always exits 0.
    """
    race_names: list[t.RaceName] = (
        [race] if race is not None else races.list_races(validate=True)
    )
    kinds = [get_kind(kind)] if kind is not None else list(KINDS.values())

    for race_name in race_names:
        stdout.print(f"[bold]{races.get_metadata(race_name).name}[/]", highlight=False)
        for asset_kind in kinds:
            found = survey(
                asset_kind,
                race_name,
                candidates_root=config.paths.candidates,
                assets_root=config.paths.assets,
                with_candidates=candidates,
            )
            stdout.print(f"  {asset_kind.name.title()}", highlight=False)
            for row in found.rows:
                _print_coverage(row)
            if found.orphans:
                stdout.print("  Unknown", highlight=False)
                for orphan in found.orphans:
                    stdout.print(f"  - {orphan.name}", highlight=False)


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
    # the Correction.
    stdout.print(correction, style="dim", markup=False)

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

    kind = get_kind("image")
    try:
        target = _resolve_target(kind, race, unit)
    except ValueError as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    if not target.description.strip():
        stderr.print(
            f"[red]Error:[/] no description for {target.name!r}, "
            "cannot generate an image"
        )
        raise SystemExit(1)

    system = (config.paths.prompts / "image.txt").read_text(encoding="utf-8")
    prompt = f"Subject: {target.human_name}.\nDetails: {target.description}\n{system}"

    count, seed = opts.resolve()
    stdout.print(f"Seed: {seed}  (rerun with --seed {seed} to reproduce)")

    # Show the composed prompt (dimmed) before sending it to the Service.
    stdout.print(prompt, style="dim", markup=False)

    try:
        generate(
            kind,
            prompt,
            race=race,
            name=target.name,
            count=count,
            seed=seed,
            candidates_root=config.paths.candidates,
            on_candidate=lambda path: stdout.print(f"Wrote {path}"),
        )
    except (OSError, ComfyUIError) as err:
        stderr.print(f"[red]Error:[/] image generation failed: {err}")
        raise SystemExit(1) from None

    stdout.print(
        f"Promote one with: spf assets promote {race} image {target.name} --pick N"
    )
