"""Checking a Kind's Targets for a Race against the two stores.

A **Survey** answers "what's left?": for each Target the Kind covers, whether a
committed Asset exists and how many Candidates are waiting. Files matching no
Target are reported as **Orphans** rather than ignored, so a Target renamed in
TOML after generation is visible instead of silent.

Derived on demand, never stored. `targets` supplies the spine; this module is
the only part that touches disk.
"""

from dataclasses import dataclass, field
from pathlib import Path

from spf.assets.kinds import Kind
from spf.assets.spine import _asset_dir
from spf.assets.targets import Target, targets
from spf.config import config
from spf.schemas import type_aliases as t


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
    assets_root: Path = config.paths.assets,
) -> Survey:
    """Return `kind`'s coverage of `race`, one row per Target.

    Rows follow `targets()` order. Raises `ValueError` for an unknown race.
    """
    asset_dir = _asset_dir(assets_root, kind, race=race)
    rows = [
        Coverage(target=target, asset=_asset_for(asset_dir, kind, target))
        for target in targets(kind, race)
    ]
    return Survey(rows=rows, orphans=[])


def _asset_for(asset_dir: Path, kind: Kind, target: Target) -> Path | None:
    """Return the committed Asset for `target`, or `None` when there is none."""
    path = asset_dir / f"{target.name}.{kind.extension}"
    return path if path.is_file() else None
