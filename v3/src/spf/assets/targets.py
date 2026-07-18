"""The Targets a Kind covers for a Race.

A **Target** is the thing an Asset depicts — a Race, a Unit, or a Model. Which
of those a given Kind applies to is declared by the Kind itself (`Kind.targets`),
so resolving them is one loop over the Race config rather than a per-command
race/unit fork.

Pure: this module reads the Race TOML and nothing else. Checking what is
actually on disk is `survey`'s job.
"""

from dataclasses import dataclass

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


def targets(kind: Kind, race: t.RaceName) -> list[Target]:
    """Return the Targets `kind` covers for `race`, race level first.

    `name` is the key that addresses the Target on the command line — the same
    one `promote` and `refine` take. Raises `ValueError` for an unknown race.
    """
    found: list[Target] = []
    if "race" in kind.targets:
        metadata = races.get_metadata(race)  # raises ValueError for unknown race
        found.append(
            Target(
                name=race,
                human_name=metadata.name,
                description=metadata.description,
                level="race",
            )
        )
    if "unit" in kind.targets:
        found.extend(
            Target(
                name=name,
                human_name=unit.name,
                description=unit.description,
                level="unit",
            )
            for name, unit in races.get_units(race).items()
        )
    return found
