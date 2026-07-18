"""The Targets a Kind covers for a Race.

A **Target** is the thing an Asset depicts — a Race, a Unit, or a Model. Which
of those a given Kind applies to is declared by the Kind itself (`Kind.targets`),
so resolving them is one loop over the Race config rather than a per-command
race/unit fork.

Pure: this module reads the Race TOML and nothing else. Checking what is
actually on disk is `survey`'s job.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from spf import races
from spf.assets.kinds import Kind, TargetLevel
from spf.schemas import type_aliases as t


@dataclass(frozen=True)
class Target:
    """One thing a Kind could have an Asset for."""

    name: str
    human_name: str
    description: str
    level: TargetLevel


class _Described(Protocol):
    """The shape every level's entries share: a display name and a blurb."""

    name: str
    description: str


# Every level resolves to a mapping of key to described entry, so the race
# level -- a single object -- is wrapped in one to match. Insertion order is
# the order Targets come back in: race, then units, then models.
_LEVELS: dict[TargetLevel, Callable[[t.RaceName], Mapping[str, _Described]]] = {
    "race": lambda race: {race: races.get_metadata(race)},
    "unit": races.get_units,
    "model": races.get_models,
}


def targets(kind: Kind, race: t.RaceName) -> list[Target]:
    """Return the Targets `kind` covers for `race`, race level first.

    `name` is the key that addresses the Target on the command line — the same
    one `promote` and `refine` take. Raises `ValueError` for an unknown race.
    """
    return [
        Target(
            name=name,
            human_name=entry.name,
            description=entry.description,
            level=level,
        )
        for level, getter in _LEVELS.items()
        if level in kind.targets
        for name, entry in getter(race).items()  # raises ValueError for unknown race
    ]
