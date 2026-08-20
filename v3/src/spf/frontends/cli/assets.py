"""Asset commands for the SteamPunkFantasy CLI.

Ships the shared, kind-agnostic `spf assets promote` and `spf assets refine`
commands, the reusable `AssetOpts` parameter set that per-kind `generate`
subcommands accept, and the first concrete generate subcommand,
`spf assets image`.
"""

import random
import textwrap
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import cyclopts
import pydantic
from codetiming import Timer

from spf import races
from spf.assets import (
    Coverage,
    Target,
    generate,
    get_kind,
    promote,
    refine,
    stage_promoted,
    survey,
    targets,
    validate_lineage,
)
from spf.assets import image as _image
from spf.assets.comfyui import ComfyUIError, ComfyUIService
from spf.assets.kinds import KINDS
from spf.assets.kinds import Kind as AssetKind
from spf.config import config
from spf.console import stderr, stdout
from spf.schemas import type_aliases as t

_SEED_BOUND = 2**31

# Marks a Target that cannot be generated for at all. A plain literal of known
# width, so the fixed-width slot it reserves is padded exactly.
_NO_BRIEF = "no brief"

# A Brief is printed under its row, indented past the "  - " bullet.
_BRIEF_INDENT = " " * 6
_BRIEF_MIN_WIDTH = 20

# UNIT, --all and --missing pick *which* Targets to generate for, so at most one
# may be given. LimitedChoice() defaults to min=0, max=1: exactly that rule.
_SELECTION = cyclopts.Group("Selection", validator=cyclopts.validators.LimitedChoice())

# `refine` always needs a Candidate to start from, and --from and --promoted are
# the two ways to name one — so unlike _SELECTION this group takes min=1,
# requiring exactly one rather than at most one.
_SOURCE = cyclopts.Group(
    "Source", validator=cyclopts.validators.LimitedChoice(min=1, max=1)
)


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


def _negative_prompt_echo() -> str:
    """Return the `Negative:` line naming where the Service reads it (D7).

    Echoed by path, not by content: unlike the composed positive prompt it is
    static and version-controlled, so naming the file keeps it discoverable
    without scrolling the varying prompt off screen. Shown project-relative
    (as `race.py` does) — short enough to read and to retype.
    """
    path = config.assets.image.negative_prompt
    try:
        shown = str(path.relative_to(config.paths.project))
    except ValueError:  # configured outside the project; absolute is all we have
        shown = str(path)
    return f"Negative: {shown}"


def _validate_lineage(_type: type, value: str | None) -> None:
    """Reject a Lineage that is not a dotted 1-based index.

    `None` is an omitted optional `--from`, which `refine --promoted` resolves
    for itself — the validator must let it through rather than parse it.
    """
    if value is None:
        return
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


@dataclass
class ImageOpts:
    """Image-specific options: env and profile selection."""

    env: str | None = None
    profile: str | None = None

    def resolve_env_profile(self) -> tuple[str, str]:
        """Return `(env, profile)` with resolution precedence.

        Per axis: config -> env var -> flag, last wins.
        """
        comfyui = config.assets.image.comfyui
        env_name = self.env if self.env is not None else comfyui.env
        profile_name = (
            self.profile or comfyui.profile or comfyui.selected(env_name).profile
        )
        return env_name, profile_name


def _resolve_image_service(
    image_opts: ImageOpts, *, validate_refine: bool = False
) -> tuple[ComfyUIService, str, str]:
    """Resolve env/profile, build the ComfyUIService, and return all three.

    Set ``validate_refine`` when the call site is a refinement (the refine
    Workflow must exist). For generate, the refine Workflow is lazily
    resolved so contributors without one can still generate.
    """
    try:
        env_name, profile_name = image_opts.resolve_env_profile()
    except ValueError as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None
    try:
        svc = _image._build_service(  # noqa: SLF001  wiring the factory
            env=env_name, profile=profile_name
        )
    except ValueError as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None
    if validate_refine:
        try:
            _image._resolve_refine(env=env_name, profile=profile_name)  # noqa: SLF001
        except ValueError as err:
            stderr.print(f"[red]Error:[/] {err}")
            raise SystemExit(1) from None
    return svc, env_name, profile_name


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
        f"[green]{lineage} (promoted)[/]" if lineage in row.promoted_from else lineage
        for lineage in row.candidates
    ]
    stdout.print(f"      {', '.join(parts)}", highlight=False, soft_wrap=True)


def _print_brief(row: Coverage) -> None:
    """Print a row's Brief, wrapped under a hanging indent, or a red note."""
    if not row.target.brief:
        stdout.print(f"{_BRIEF_INDENT}[red]No brief[/]", highlight=False)
        return
    # Wrapped here rather than by Rich so the continuation lines carry the same
    # indent as the first without the block being right-filled to the terminal
    # width. A Brief is already normalized to a single paragraph by `targets()`,
    # so there are no blank lines or hard breaks for `wrap` to mangle.
    width = max(stdout.width - len(_BRIEF_INDENT), _BRIEF_MIN_WIDTH)
    for line in textwrap.wrap(row.target.brief, width=width):
        stdout.print(
            f"{_BRIEF_INDENT}{line}",
            style="dim",
            # A Brief is arbitrary authored prose: a `[` in it must not parse
            # as a Rich tag and swallow the rest of the line.
            markup=False,
            highlight=False,
            soft_wrap=True,  # already wrapped; let it through untouched
        )


def _print_coverage(row: Coverage) -> None:
    """Print one Coverage row: key first, human name dimmed, then status."""
    status = "[green]\N{CHECK MARK}[/]" if row.asset else "[red]\N{BALLOT X}[/]"
    # Asymmetric (ADR 0014): only a Brief-less row is marked, so a fully
    # briefed race renders exactly as it did before the column existed. The
    # slot is still occupied when there is nothing to say, so the candidate
    # count starts at the same column on every row.
    brief = " " * len(_NO_BRIEF) if row.target.brief else f"[red]{_NO_BRIEF}[/]"
    count = f"{len(row.candidates)} candidates" if row.candidates else ""
    # The name columns pad the *plain* value before the markup wraps it:
    # padding an already-marked-up string counts the tag characters and
    # misaligns every column after it.
    stdout.print(
        # rstrip so an unmarked row with no count does not trail the empty
        # slot's padding; a row that has a count is unaffected, so the slot
        # still lines the counts up.
        f"  - {row.target.name:<32} [dim]{row.target.human_name:<32}[/]"
        f" {status} {brief} {count}".rstrip(),
        highlight=False,
        soft_wrap=True,  # a coverage row is scanned or piped, never reflowed
    )


def list_assets(
    race: t.RaceName | None = None,
    *,
    kind: Kind | None = None,
    candidates: bool = False,
    briefs: bool = False,
) -> None:
    """Report which Targets have Assets, and how many Candidates are waiting.

    RACE restricts the report to one race; omitted, every validating race is
    covered. `--kind` restricts it to one registered Asset kind, and
    `--candidates` expands each row into its Candidate Lineages, marking the
    one the Asset was promoted from.

    A Target with no Brief — the authored text its kind generates from — is
    marked `no brief`: nothing can be generated for it until one is written.
    `--briefs` expands each row into its Brief, for proofreading the text
    before spending generation time on it.

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
                # Brief first, then Lineages: mirrors the row's own columns.
                if briefs:
                    _print_brief(row)
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


@contextmanager
def _timed_candidates() -> Iterator[Callable[[Path], None]]:
    """Yield an `on_candidate` reporting each Candidate with its elapsed time.

    The interval is the gap between two Service callbacks, so it is stopped and
    restarted per candidate rather than wrapped in a scope of its own. A job
    yielding several images reports the elapsed time against the first.
    """
    timer = Timer(logger=None)

    def report(path: Path) -> None:
        stdout.print(
            f"Wrote {path} ({timer.stop():.1f}s)",
            highlight=False,
            soft_wrap=True,  # a path is copied or piped, never reflowed
        )
        timer.start()

    timer.start()
    try:
        yield report
    finally:
        # `report` restarts the timer after the last Candidate and the Service
        # can raise mid-batch, so the timer is always still running here. The
        # Timer is per-context, so stopping it is hygiene rather than a fix for
        # anything observable.
        timer.stop()


def _refine_source(
    kind: AssetKind, *, race: t.RaceName, name: str, from_: str | None, promoted: bool
) -> str:
    """Return the Lineage a refinement starts from, staging the Asset if asked.

    With `--promoted` the committed Asset is copied back into the Candidate
    store first and reported by name, so the refinement itself stays the
    ordinary Candidate-to-Candidate operation. Raises `ValueError` when there
    is no promoted Asset to stage.
    """
    if not promoted:
        if from_ is None:
            # Narrows `from_` to `str`; _SOURCE already rules this out.
            msg = "either --from or --promoted is required"
            raise ValueError(msg)
        return from_

    lineage = stage_promoted(
        kind,
        race=race,
        name=name,
        candidates_root=config.paths.candidates,
        assets_root=config.paths.assets,
    )
    stdout.print(f"Copied promoted asset to {name}.{lineage}.{kind.extension}")
    return lineage


def refine_asset(  # noqa: PLR0913  mirrors promote, plus the Correction and opts
    race: t.RaceName,
    kind: Kind,
    name: str,
    correction: str,
    *,
    from_: Annotated[
        Lineage | None, cyclopts.Parameter(name="--from", group=_SOURCE)
    ] = None,
    promoted: Annotated[bool, cyclopts.Parameter(group=_SOURCE)] = False,
    opts: Annotated[AssetOpts | None, cyclopts.Parameter(name="*")] = None,
    image_opts: Annotated[ImageOpts | None, cyclopts.Parameter(name="*")] = None,
) -> None:
    """Refine an existing Candidate by applying a CORRECTION to it.

    RACE is the race the Asset belongs to, KIND its Asset kind, NAME its base
    file name, and CORRECTION the edit to apply ("make the hat brass instead
    of leather"). `--from` picks the Candidate to refine by Lineage, the same
    dotted index `promote --pick` takes; `--promoted` instead refines the
    committed Asset, staging a copy of it into the Candidate store first.
    Exactly one of the two is required.

    The Correction is the whole prompt — no `prompts/image.txt` preamble and no
    race description, because an instruction-edit model is trained on
    instructions. Results land under the derived name `NAME.LINEAGE`, so
    refining `2` writes `2.1`, `2.2`, … and the original is left alone.

    `--env` and `--profile` apply only to image assets and select the ComfyUI
    Environment and Profile. Passing `--profile` with a non-image kind errors.
    """
    asset_kind = get_kind(kind)
    image_opts = image_opts or ImageOpts()

    if (
        image_opts.env is not None or image_opts.profile is not None
    ) and asset_kind.name != "image":
        stderr.print("[red]Error:[/] --env/--profile apply only to image assets")
        raise SystemExit(1) from None

    svc: ComfyUIService | None = None
    env_name: str | None = None
    profile_name: str | None = None
    if asset_kind.name == "image":
        svc, env_name, profile_name = _resolve_image_service(
            image_opts, validate_refine=True
        )

    count, seed = (opts or AssetOpts()).resolve()

    if env_name is not None and profile_name is not None:
        stdout.print(f"Env: {env_name}  Profile: {profile_name}")

    # Show what is actually sent (dimmed), matching `image`; here it is just
    # the Correction. The Negative Prompt is an image concern, so name its file
    # only when an image is what is being refined.
    stdout.print(correction, style="dim", markup=False)
    if asset_kind.name == "image":
        stdout.print(_negative_prompt_echo(), style="dim", soft_wrap=True)

    try:
        lineage = _refine_source(
            asset_kind, race=race, name=name, from_=from_, promoted=promoted
        )
        with _timed_candidates() as on_candidate:
            refine(
                asset_kind,
                correction,
                race=race,
                name=name,
                lineage=lineage,
                count=count,
                seed=seed,
                candidates_root=config.paths.candidates,
                on_candidate=on_candidate,
                service=svc,
            )
    except (OSError, ComfyUIError, TypeError, ValueError) as err:
        stderr.print(f"[red]Error:[/] refinement failed: {err}")
        raise SystemExit(1) from None

    # The *resolved* Lineage: with --promoted there is no `from_` to name, and
    # interpolating it would render `--pick None.N`.
    stdout.print(
        f"Promote one with: spf assets promote {race} {kind} {name} --pick {lineage}.N"
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


def image(  # noqa: PLR0913  CLI surface, parameters are fixed
    race: t.RaceName,
    unit: Annotated[str | None, cyclopts.Parameter(group=_SELECTION)] = None,
    *,
    all_: Annotated[bool, cyclopts.Parameter(name="--all", group=_SELECTION)] = False,
    missing: Annotated[bool, cyclopts.Parameter(group=_SELECTION)] = False,
    opts: Annotated[AssetOpts | None, cyclopts.Parameter(name="*")] = None,
    image_opts: Annotated[ImageOpts | None, cyclopts.Parameter(name="*")] = None,
) -> None:
    """Generate image Candidates for a RACE, or a UNIT of it.

    `--all` covers the race and every unit; `--missing` covers every Target
    with no promoted Asset yet, the race-level image included. The two, and a
    named UNIT, are mutually exclusive.

    The prompt is composed from the configured preamble file
    (`assets.image.prompt`, by default `prompts/image.txt`) plus the target's
    name and Brief; a target without a Brief is warned about and skipped.

    `--env` and `--profile` select the ComfyUI Environment and Profile.
    Resolution order per axis: config -> env var -> flag, last wins.
    """
    opts = opts or AssetOpts()
    image_opts = image_opts or ImageOpts()
    kind = get_kind("image")

    # Arguments are validated before the Service is built, so a mistyped unit
    # is reported as such rather than as whatever the machine's ComfyUI
    # Environment happens to be missing.
    try:
        selected = _image_targets(kind, race, unit, all_=all_, missing=missing)
    except ValueError as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    svc, env_name, profile_name = _resolve_image_service(image_opts)

    # Partition before generating rather than skipping mid-loop (ADR 0015), so
    # the batch's real shape is on screen before any GPU time is spent on it.
    briefed: list[Target] = []
    for target in selected:
        if target.brief:
            briefed.append(target)
        else:
            stderr.print(f"[yellow]Warning:[/] no brief for {target.name!r}, skipping")

    if not briefed:
        # Exiting 0 in silence would read as a crash rather than an outcome.
        stdout.print("Nothing to generate.")
        return

    for target in briefed:
        if len(briefed) > 1:
            stdout.print(f"[green]{target.name}[/]")
        _generate_image(kind, race, target, opts, svc, env_name, profile_name)


def _generate_image(  # noqa: PLR0913  internal seam, parameters are fixed
    kind: AssetKind,
    race: t.RaceName,
    target: Target,
    opts: AssetOpts,
    svc: ComfyUIService,
    env_name: str,
    profile_name: str,
) -> None:
    """Generate Candidates for one Target, reporting each as it lands."""
    # Unreachable from `image()`, which partitions Brief-less Targets out and
    # warns instead (ADR 0015). Kept as the genuine error path for any other
    # caller rather than replaced by an assert.
    if not target.brief:  # already normalized by targets(), so no .strip()
        stderr.print(
            f"[red]Error:[/] no brief for {target.name!r}, cannot generate an image"
        )
        raise SystemExit(1)

    system = config.assets.image.prompt.read_text(encoding="utf-8")
    prompt = f"Subject: {target.human_name}.\nDetails: {target.brief}\n{system}"

    count, seed = opts.resolve()
    stdout.print(f"Seed: {seed}  (rerun with --seed {seed} to reproduce)")
    stdout.print(f"Env: {env_name}  Profile: {profile_name}")

    # Show the composed prompt (dimmed) before sending it to the Service.
    stdout.print(prompt, style="dim", markup=False)
    stdout.print(_negative_prompt_echo(), style="dim", soft_wrap=True)

    try:
        with _timed_candidates() as on_candidate:
            generate(
                kind,
                prompt,
                race=race,
                name=target.name,
                count=count,
                seed=seed,
                candidates_root=config.paths.candidates,
                on_candidate=on_candidate,
                service=svc,
            )
    except (OSError, ComfyUIError) as err:
        stderr.print(f"[red]Error:[/] image generation failed: {err}")
        raise SystemExit(1) from None

    stdout.print(
        f"Promote one with: spf assets promote {race} image {target.name} --pick N"
    )
