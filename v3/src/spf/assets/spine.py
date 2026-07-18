"""The assets seams: generate Candidates, refine one, then promote one.

All three are kind-agnostic — behavior comes entirely from the `Kind`
record. A Kind's layout is `<race>/[<subdir>/]<name>.<extension>`; Candidates
insert a 1-based `.<index>` before the extension so the same layout addresses
both stores. The index is allocated past whatever is already on disk rather
than restarting each run, so a Candidate is never overwritten (ADR 0013).
A Refinement generates under the derived name `<name>.<lineage>`, which is
that same rule applied twice, so Lineage needs no store of its own.

`refine` is available only for Kinds whose Service implements the optional
`Refiner` protocol; the others raise a clean `TypeError`.
"""

import re
import shutil
from collections.abc import Callable
from pathlib import Path

from spf.assets.kinds import Kind, Refiner
from spf.config import config

LINEAGE_PATTERN = re.compile(r"^[1-9][0-9]*(\.[1-9][0-9]*)*$")
INDEX_PATTERN = re.compile(r"^[1-9][0-9]*$")


def validate_lineage(lineage: str) -> str:
    """Return `lineage` unchanged, or raise `ValueError` if it is malformed.

    A **Lineage** is a dotted, 1-based Candidate index (`2`, `2.1`, `2.1.3`)
    recording derivation: `2.1` is the first Candidate of the Refinement of
    Candidate `2`. Leading zeros and empty components are rejected, so a typo
    fails here rather than as a confusing missing-file error.
    """
    if not LINEAGE_PATTERN.match(lineage):
        msg = (
            f"Malformed lineage {lineage!r}: expected a dotted 1-based index, "
            "such as '2' or '2.1'"
        )
        raise ValueError(msg)
    return lineage


def _split_lineage(stem: str) -> tuple[str, str] | None:
    """Return `(target_name, lineage)` for a Candidate stem, or `None`.

    Splits from the *right* on components that are whole 1-based indices, so a
    Target name that itself ends in digits (`ork_char_b1`, `e34`) keeps them.
    `None` means the stem carries no Lineage at all.
    """
    parts = stem.split(".")
    cut = len(parts)
    while cut > 1 and INDEX_PATTERN.match(parts[cut - 1]):
        cut -= 1
    if cut == len(parts):
        return None
    return ".".join(parts[:cut]), ".".join(parts[cut:])


def _asset_dir(root: Path, kind: Kind, *, race: str) -> Path:
    """Return the directory a Kind's files live in under `root` for `race`."""
    directory = root / race
    if kind.subdir is not None:
        directory = directory / kind.subdir
    return directory


def _next_index(directory: Path, kind: Kind, *, name: str) -> int:
    """Return the index a new Candidate of `name` should take.

    One past the highest first-component Lineage already present *anywhere*
    under `name`, so a surviving refinement (`ork.4.1`) reserves its parent's
    number even when the parent itself was deleted. Indices are never reused
    and gaps are never filled (see ADR 0013).
    """
    highest = 0
    # The `.` separator keeps prefix-siblings apart: globbing `grunt.*` will
    # not match `grunt_carrier.1.txt`.
    for path in directory.glob(f"{name}.*.{kind.extension}"):
        split = _split_lineage(path.name[: -len(kind.extension) - 1])
        if split is None:
            continue
        highest = max(highest, int(split[1].split(".")[0]))
    return highest + 1


def _candidate_writer(
    directory: Path,
    kind: Kind,
    *,
    name: str,
    on_candidate: Callable[[Path], None] | None,
) -> tuple[list[Path], Callable[[bytes | str], None]]:
    """Return `(paths, persist)` for writing Candidates as a Service yields them.

    `persist` writes each value to `<name>.<index>.<extension>`, inferring
    text-vs-binary mode from the value's type, and appends the path to `paths`.
    The first index comes from `_next_index`, so a run appends past whatever is
    already on disk instead of overwriting it. It is computed once, up front:
    the files this writer itself creates must not shift the numbering. Shared
    by `generate` and `refine`, which differ only in which Service call drives
    it.
    """
    directory.mkdir(parents=True, exist_ok=True)
    start = _next_index(directory, kind, name=name)
    paths: list[Path] = []

    def persist(value: bytes | str) -> None:
        path = directory / f"{name}.{start + len(paths)}.{kind.extension}"
        if isinstance(value, bytes):
            path.write_bytes(value)
        else:
            path.write_text(value, encoding="utf-8")
        paths.append(path)
        if on_candidate is not None:
            on_candidate(path)

    return paths, persist


def generate(  # noqa: PLR0913  the seam's parameters are fixed by the assets-foundation spec
    kind: Kind,
    source: str,
    *,
    race: str,
    name: str,
    count: int,
    seed: int | None = None,
    candidates_root: Path = config.paths.candidates,
    on_candidate: Callable[[Path], None] | None = None,
) -> list[Path]:
    """Generate `count` Candidates for `source` and write them to disk.

    Each generated value is written to
    `candidates_root/<race>/[<subdir>/]<name>.<index>.<extension>`, inferring
    text-vs-binary mode from the value's type, *as soon as the Service produces
    it* — so a slow batch persists each Candidate rather than waiting for the
    whole run. Indices append past the highest Lineage already present under
    `name`, so an existing Candidate is never overwritten and gaps are never
    filled (ADR 0013). `on_candidate` (when given) is called with each path
    right after it is written. Returns the written paths in order. `seed` is threaded
    straight to the Service (see `Service`).
    """
    directory = _asset_dir(candidates_root, kind, race=race)
    paths, persist = _candidate_writer(
        directory, kind, name=name, on_candidate=on_candidate
    )
    kind.service.generate(source, count, seed=seed, on_result=persist)
    return paths


def refine(  # noqa: PLR0913  mirrors `generate`, plus the Lineage being refined
    kind: Kind,
    source: str,
    *,
    race: str,
    name: str,
    lineage: str,
    count: int,
    seed: int | None = None,
    candidates_root: Path = config.paths.candidates,
    on_candidate: Callable[[Path], None] | None = None,
) -> list[Path]:
    """Refine the Candidate at `lineage`, writing `count` new Candidates.

    `source` is the Correction, passed to the Service verbatim — no Race
    description is looked up, because an instruction-edit model takes the
    Correction as its whole prompt (ADR 0010).

    The new Candidates are generated under the *derived* name
    `<name>.<lineage>`, so a first refinement of Candidate `2` of `grunt`
    writes `grunt.2.1`, `grunt.2.2`, … and a second one continues at
    `grunt.2.3` rather than restarting. The source Candidate is never
    overwritten, and the derivation reads straight off the filename. Chaining
    follows the same rule, so `2.1` refines to `2.1.1`.

    Raises `ValueError` when `lineage` is malformed or its Candidate is
    missing, and `TypeError` when the Kind's Service cannot refine.
    """
    validate_lineage(lineage)
    service = kind.service
    if not isinstance(service, Refiner):
        msg = f"Kind {kind.name!r} does not support refinement"
        raise TypeError(msg)

    directory = _asset_dir(candidates_root, kind, race=race)
    init = directory / f"{name}.{lineage}.{kind.extension}"
    if not init.is_file():
        msg = f"No candidate to refine at {init} (lineage {lineage})"
        raise ValueError(msg)

    paths, persist = _candidate_writer(
        directory, kind, name=f"{name}.{lineage}", on_candidate=on_candidate
    )
    service.refine(source, init.read_bytes(), count, seed=seed, on_result=persist)
    return paths


def promote(  # noqa: PLR0913  the seam's parameters are fixed by the assets-foundation spec
    kind: Kind,
    *,
    race: str,
    name: str,
    pick: str,
    candidates_root: Path = config.paths.candidates,
    assets_root: Path = config.paths.assets,
) -> Path:
    """Promote the picked Candidate into the committed Asset store.

    Copies `<race>/[<subdir>/]<name>.<pick>.<extension>` from the candidates
    store to `<race>/[<subdir>/]<name>.<extension>` in the assets store,
    bytes-for-bytes. `pick` is a Lineage — a dotted 1-based index (`2`, `2.1`),
    so a Refinement's Candidate promotes exactly like an original's. An
    existing Asset is overwritten silently. Raises `ValueError` when `pick` is
    malformed or the picked Candidate is missing.
    """
    validate_lineage(pick)
    candidate = (
        _asset_dir(candidates_root, kind, race=race) / f"{name}.{pick}.{kind.extension}"
    )
    if not candidate.is_file():
        msg = f"No candidate to promote at {candidate} (pick {pick})"
        raise ValueError(msg)

    asset = _asset_dir(assets_root, kind, race=race) / f"{name}.{kind.extension}"
    asset.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidate, asset)
    return asset


def stage_promoted(
    kind: Kind,
    *,
    race: str,
    name: str,
    candidates_root: Path = config.paths.candidates,
    assets_root: Path = config.paths.assets,
) -> str:
    """Copy the promoted Asset back into the Candidate store, returning its Lineage.

    The exact inverse of `promote`: a plain `copyfile` the other way, taking
    the next free index (see `_next_index`) so the Asset becomes an ordinary
    Candidate addressable by Lineage. Raises `ValueError` when the Target has
    no promoted Asset.
    """
    asset = _asset_dir(assets_root, kind, race=race) / f"{name}.{kind.extension}"
    if not asset.is_file():
        msg = f"No promoted asset to stage at {asset}"
        raise ValueError(msg)

    directory = _asset_dir(candidates_root, kind, race=race)
    directory.mkdir(parents=True, exist_ok=True)
    lineage = str(_next_index(directory, kind, name=name))
    shutil.copyfile(asset, directory / f"{name}.{lineage}.{kind.extension}")
    return lineage
