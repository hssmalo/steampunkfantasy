"""Checking a Kind's Targets for a Race against the two stores.

A **Survey** answers "what's left?": for each Target the Kind covers, whether a
committed Asset exists and how many Candidates are waiting. Files matching no
Target are reported as **Orphans** rather than ignored, so a Target renamed in
TOML after generation is visible instead of silent.

Derived on demand, never stored. `targets` supplies the spine; this module is
the only part that touches disk.
"""

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from spf.assets.kinds import Kind
from spf.assets.spine import _asset_dir
from spf.assets.targets import Target, targets
from spf.config import config
from spf.schemas import type_aliases as t

_INDEX_PATTERN = re.compile(r"^[1-9][0-9]*$")


@dataclass(frozen=True)
class Coverage:
    """One Target's line in a Survey."""

    target: Target
    asset: Path | None
    candidates: list[str] = field(default_factory=list)
    """Lineages of the Candidates waiting for this Target, numerically sorted."""
    promoted_from: list[str] = field(default_factory=list)
    """Lineages byte-identical to the Asset; empty when not looked for."""


@dataclass(frozen=True)
class Survey:
    """One Kind's coverage of one Race."""

    rows: list[Coverage]
    orphans: list[Path]


def survey(
    kind: Kind,
    race: t.RaceName,
    *,
    candidates_root: Path = config.paths.candidates,
    assets_root: Path = config.paths.assets,
    with_candidates: bool = False,
) -> Survey:
    """Return `kind`'s coverage of `race`, one row per Target.

    Rows follow `targets()` order. `with_candidates` additionally recovers, by
    digest, which Candidate each Asset was promoted from — the expensive part,
    so it is off by default (ADR 0012). Raises `ValueError` for an unknown race.
    """
    asset_dir = _asset_dir(assets_root, kind, race=race)
    candidate_dir = _asset_dir(candidates_root, kind, race=race)
    waiting = _candidates_by_name(candidate_dir, kind)
    found = targets(kind, race)
    rows = []
    for target in found:
        asset = _asset_for(asset_dir, kind, target)
        lineages = sorted(waiting.get(target.name, []), key=_lineage_key)
        rows.append(
            Coverage(
                target=target,
                asset=asset,
                candidates=lineages,
                promoted_from=(
                    _promoted_from(asset, candidate_dir, kind, target, lineages)
                    if with_candidates and asset is not None
                    else []
                ),
            )
        )
    known = {target.name for target in found}
    orphans = [
        path
        for path in sorted(asset_dir.glob(f"*.{kind.extension}"))
        if path.name[: -len(kind.extension) - 1] not in known
    ]
    if with_candidates:
        orphans += [
            candidate_dir / f"{name}.{lineage}.{kind.extension}"
            for name in sorted(waiting.keys() - known)
            for lineage in sorted(waiting[name], key=_lineage_key)
        ]
    return Survey(rows=rows, orphans=orphans)


def _asset_for(asset_dir: Path, kind: Kind, target: Target) -> Path | None:
    """Return the committed Asset for `target`, or `None` when there is none."""
    path = asset_dir / f"{target.name}.{kind.extension}"
    return path if path.is_file() else None


def _promoted_from(
    asset: Path,
    candidate_dir: Path,
    kind: Kind,
    target: Target,
    lineages: list[str],
) -> list[str]:
    """Return every Lineage byte-identical to `asset`.

    `promote` is a plain copy, so the Asset matches the Candidate it came from.
    Seeds are deterministic, so two Candidates can collide — all matches are
    reported rather than one guessed (ADR 0012).
    """
    digest = _digest(asset)
    matches = []
    for lineage in lineages:
        path = candidate_dir / f"{target.name}.{lineage}.{kind.extension}"
        if path.is_file() and _digest(path) == digest:
            matches.append(lineage)
    return matches


def _digest(path: Path) -> bytes:
    """Return the SHA-256 digest of `path`."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").digest()


def _lineage_key(lineage: str) -> tuple[int, ...]:
    """Return the sort key for a Lineage: `2.1` sorts before `10`, not after."""
    return tuple(int(part) for part in lineage.split("."))


def _split_lineage(stem: str) -> tuple[str, str] | None:
    """Return `(target_name, lineage)` for a Candidate stem, or `None`.

    Splits from the *right* on components that are whole 1-based indices, so a
    Target name that itself ends in digits (`ork_char_b1`, `e34`) keeps them.
    `None` means the stem carries no Lineage at all.
    """
    parts = stem.split(".")
    cut = len(parts)
    while cut > 1 and _INDEX_PATTERN.match(parts[cut - 1]):
        cut -= 1
    if cut == len(parts):
        return None
    return ".".join(parts[:cut]), ".".join(parts[cut:])


def _candidates_by_name(candidate_dir: Path, kind: Kind) -> dict[str, list[str]]:
    """Return the Lineages waiting in `candidate_dir`, keyed by Target name."""
    waiting: dict[str, list[str]] = defaultdict(list)
    for path in sorted(candidate_dir.glob(f"*.{kind.extension}")):
        split = _split_lineage(path.name[: -len(kind.extension) - 1])
        if split is not None:
            waiting[split[0]].append(split[1])
    return waiting
