"""The assets seams: generate Candidates, then promote one into the store.

Both functions are kind-agnostic — behavior comes entirely from the :class:`Kind`
record. A Kind's layout is ``<race>/[<subdir>/]<name>.<extension>``; Candidates
insert a 1-based ``.<index>`` before the extension so the same layout addresses
both stores.
"""

import shutil
from collections.abc import Callable
from pathlib import Path

from spf.assets.kinds import Kind
from spf.config import config


def _asset_dir(root: Path, kind: Kind, race: str) -> Path:
    """Return the directory a Kind's files live in under ``root`` for ``race``."""
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
    """Generate ``count`` Candidates for ``source`` and write them to disk.

    Each generated value is written to
    ``candidates_root/<race>/[<subdir>/]<name>.<index>.<extension>`` with a
    1-based index, inferring text-vs-binary mode from the value's type, *as soon
    as the Service produces it* — so a slow batch persists each Candidate rather
    than waiting for the whole run. Existing candidate files are overwritten
    silently. ``on_candidate`` (when given) is called with each path right after
    it is written. Returns the written paths in order. ``seed`` is threaded
    straight to the Service (see :class:`Service`).
    """
    directory = _asset_dir(candidates_root, kind, race)
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
    pick: int,
    candidates_root: Path = config.paths.candidates,
    assets_root: Path = config.paths.assets,
) -> Path:
    """Promote the picked Candidate into the committed Asset store.

    Copies ``<race>/[<subdir>/]<name>.<pick>.<extension>`` from the candidates
    store to ``<race>/[<subdir>/]<name>.<extension>`` in the assets store,
    bytes-for-bytes. ``pick`` is 1-based. An existing Asset is overwritten
    silently. Raises :class:`ValueError` when the picked Candidate is missing.
    """
    candidate = (
        _asset_dir(candidates_root, kind, race) / f"{name}.{pick}.{kind.extension}"
    )
    if not candidate.is_file():
        msg = f"No candidate to promote at {candidate} (pick {pick})"
        raise ValueError(msg)

    asset = _asset_dir(assets_root, kind, race) / f"{name}.{kind.extension}"
    asset.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidate, asset)
    return asset
