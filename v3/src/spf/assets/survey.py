"""Checking a Kind's Targets for a Race against the two stores.

A **Survey** answers "what's left?": for each Target the Kind covers, whether a
committed Asset exists and how many Candidates are waiting. Files matching no
Target are reported as **Orphans** rather than ignored, so a Target renamed in
TOML after generation is visible instead of silent.

Derived on demand, never stored. `targets` supplies the spine; this module is
the only part that touches disk.
"""

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
) -> Survey:
    """Return `kind`'s coverage of `race`, one row per Target.

    Rows follow `targets()` order. Raises `ValueError` for an unknown race.
    """
    asset_dir = _asset_dir(assets_root, kind, race=race)
    waiting = _candidates_by_name(_asset_dir(candidates_root, kind, race=race), kind)
    rows = [
        Coverage(
            target=target,
            asset=_asset_for(asset_dir, kind, target),
            candidates=sorted(waiting.get(target.name, []), key=_lineage_key),
        )
        for target in targets(kind, race)
    ]
    return Survey(rows=rows, orphans=[])


def _asset_for(asset_dir: Path, kind: Kind, target: Target) -> Path | None:
    """Return the committed Asset for `target`, or `None` when there is none."""
    path = asset_dir / f"{target.name}.{kind.extension}"
    return path if path.is_file() else None


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
