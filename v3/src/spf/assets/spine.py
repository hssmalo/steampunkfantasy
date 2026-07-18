"""The assets seams: generate Candidates, then promote one into the store.

Both functions are kind-agnostic — behavior comes entirely from the `Kind`
record. A Kind's layout is `<race>/[<subdir>/]<name>.<extension>`; Candidates
insert a 1-based `.<index>` before the extension so the same layout addresses
both stores.
"""

import re
import shutil
from collections.abc import Callable
from pathlib import Path

from spf.assets.kinds import Kind
from spf.config import config

LINEAGE_PATTERN = re.compile(r"^[1-9][0-9]*(\.[1-9][0-9]*)*$")


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


def _asset_dir(root: Path, kind: Kind, *, race: str) -> Path:
    """Return the directory a Kind's files live in under `root` for `race`."""
    directory = root / race
    if kind.subdir is not None:
        directory = directory / kind.subdir
    return directory


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
    `candidates_root/<race>/[<subdir>/]<name>.<index>.<extension>` with a
    1-based index, inferring text-vs-binary mode from the value's type, *as soon
    as the Service produces it* — so a slow batch persists each Candidate rather
    than waiting for the whole run. Existing candidate files are overwritten
    silently. `on_candidate` (when given) is called with each path right after
    it is written. Returns the written paths in order. `seed` is threaded
    straight to the Service (see `Service`).
    """
    directory = _asset_dir(candidates_root, kind, race=race)
    directory.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []

    def _persist(value: bytes | str) -> None:
        path = directory / f"{name}.{len(paths) + 1}.{kind.extension}"
        if isinstance(value, bytes):
            path.write_bytes(value)
        else:
            path.write_text(value, encoding="utf-8")
        paths.append(path)
        if on_candidate is not None:
            on_candidate(path)

    kind.service.generate(source, count, seed=seed, on_result=_persist)
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
