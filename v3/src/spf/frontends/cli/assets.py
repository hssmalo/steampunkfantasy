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
import pydantic

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

# UNIT, --all and --missing pick *which* Targets to generate for, so at most one
# may be given. LimitedChoice() defaults to min=0, max=1: exactly that rule.
_SELECTION = cyclopts.Group("Selection", validator=cyclopts.validators.LimitedChoice())


def add_commands(app: cyclopts.App) -> None:
    """Add asset commands to the CLI."""
    app.command(list_assets, name="list")
    app.command(promote_asset, name="promote")
    app.command(refine_asset, name="refine")
    app.command(image, name="image")


def _validate_kind(_type: type, value: str | None) -> None:
    """Reject a KIND that is not registered, surfacing the known kinds.

    `None` is an omitted optional `--kind`, which means "every registered
    kind" — the validator must let it through rather than look it up.
    """
    if value is None:
        return
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

    `race` must be a known race; `unit` (when given) a known key of it.
    Raises `ValueError` mirroring `get_race` for unknown names.

    Matching is by name across every level the Kind declares, rather than a
    hardcoded race/unit fork, so a Kind that declares `model` resolves without
    touching this helper. `targets()` yields the race level first, so a unit
    keyed like its own race cannot shadow it.
    """
    found = targets(kind, race)  # raises ValueError for unknown race
    wanted = race if unit is None else unit
    for target in found:
        if target.name == wanted:
            return target
    available = ", ".join(t_.name for t_ in found if t_.level != "race")
    msg = f"Unknown unit '{unit}' for race '{race}'. Available units: {available}"
    raise ValueError(msg)


def _print_lineages(row: Coverage) -> None:
    """Print a row's Candidate Lineages, flat and numerically sorted."""
    parts = [
        f"[green]{lineage}←promoted[/]" if lineage in row.promoted_from else lineage
        for lineage in row.candidates
    ]
    stdout.print(f"      {'  '.join(parts)}", highlight=False, soft_wrap=True)


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

    Missing Assets are a normal state, so reporting coverage always exits 0.
    A RACE named explicitly but failing to validate cannot be reported at all,
    and exits 1; the omitted-RACE sweep skips such races silently (ADR 0004).
    """
    race_names: list[t.RaceName] = (
        [race] if race is not None else races.list_races(validate=True)
    )
    kinds = [get_kind(kind)] if kind is not None else list(KINDS.values())

    for race_name in race_names:
        try:
            # `get_race` validates the whole RaceConfig, so this one guard also
            # covers the `survey` calls below.
            metadata = races.get_metadata(race_name)
        except pydantic.ValidationError:
            stderr.print(
                f"[red]Error:[/] race '{race_name}' does not validate, "
                "so its coverage cannot be reported"
            )
            raise SystemExit(1) from None
        stdout.print(f"[bold]{metadata.name}[/]", highlight=False)
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
                if candidates and row.candidates:
                    _print_lineages(row)
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


def _image_targets(
    kind: AssetKind, race: t.RaceName, unit: str | None, *, all_: bool, missing: bool
) -> list[Target]:
    """Return the Targets one `image` invocation should generate for.

    Exactly one selector applies, enforced by `_SELECTION` before we get here:
    `--all` takes every Target, `--missing` every Target with no promoted Asset
    (the race-level one included), and otherwise it is the single named Target.
    """
    if all_:
        return targets(kind, race)
    if missing:
        found = survey(
            kind,
            race,
            candidates_root=config.paths.candidates,
            assets_root=config.paths.assets,
        )
        return [row.target for row in found.rows if row.asset is None]
    return [_resolve_target(kind, race, unit)]


def image(
    race: t.RaceName,
    unit: Annotated[str | None, cyclopts.Parameter(group=_SELECTION)] = None,
    *,
    all_: Annotated[bool, cyclopts.Parameter(name="--all", group=_SELECTION)] = False,
    missing: Annotated[bool, cyclopts.Parameter(group=_SELECTION)] = False,
    opts: Annotated[AssetOpts | None, cyclopts.Parameter(name="*")] = None,
) -> None:
    """Generate image Candidates for a RACE, or a UNIT of it.

    `--all` covers the race and every unit; `--missing` covers every Target
    with no promoted Asset yet, the race-level image included. The two, and a
    named UNIT, are mutually exclusive.

    The prompt is composed from `prompts/image.txt` plus the target's name
    and description; a target without a description is a hard error.
    """
    opts = opts or AssetOpts()
    kind = get_kind("image")

    try:
        selected = _image_targets(kind, race, unit, all_=all_, missing=missing)
    except ValueError as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    for target in selected:
        if len(selected) > 1:
            stdout.print(f"[green]{target.name}[/]")
        _generate_image(kind, race, target, opts)


def _generate_image(
    kind: AssetKind, race: t.RaceName, target: Target, opts: AssetOpts
) -> None:
    """Generate Candidates for one Target, reporting each as it lands."""
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
