"""Type aliases for SteamPunkFantasy."""

from typing import Annotated, Literal, Self, cast

from pydantic import BeforeValidator

from spf.schemas import StrictModel

type Angles[T] = list[T]
type DieResult = str
type Die = str
type FireOrder = list[str]
type MovementOrder = list[str]
type ArmorPenetration = int | Literal["N/A"]
type UnitName = str
type ModelName = str
type EquipmentName = str
type DamageTable = list[str]

type RaceName = Literal[
    "abomination", "darkelf", "dwarf", "elf", "gnome", "goblin", "ogre", "ork"
]
type DamageTableName = Literal["crew", "critical", "inner", "psychic", "regular"]
type EquipmentHolder = Literal[
    "Independent",
    "Grenades",
    "Hands",
    "Mechanical Tentacles",
    "Shared",
    "Specialization",
    "Tentacles",
    "Minor Gun",
    "Reserve Melee",
    "Training"
]
type Speed = Literal[
    "all",
    "rest",
    "still",
    "crawl",
    "slow",
    "fast",
    "still_flying",
    "slow_flying",
    "fast_flying",
]
type Size = Literal["Tiny", "Small", "Medium", "Large", "Huge", "Enormous"]
type UnitSpecial = Literal[
    "Hans Sverre's favorite rule",
    "Hans Sverre's second favorite rule",
    "Immunity",
    "Resistance",
    "Improved Resistance",
    "Improved Resistance (2)",
    "Protection",
    "Take Cover",
    "Camouflage",
    "Evation",
    "Hidden",
    "Improved Hide",
    "Movement",
    "Chase",
    "Pet",
    "Transport",
    "Tow",
    "Fire Order",
    "Reload",
    "Regeneration",
    "Heal",
    "Heal (2)",
    "Repair",
    "Repairing",
    "Suicide",
    "LoS",
    "Terror",
    "Poison Cloud",
    "Fog",
    "Illusion",
    "Tentacle",
    "Darkelf Officer",
    "Officer",
    "Officer 2",
    "Officer Order",
    "Stacking Limit",    
    "Spawn",
    "Transfer",
    "Vulnerability",
    "Setup",
    "Forward Position",
    "Activate",
    "Note",


]

type ModelSpecial = Literal[
    "To Hit",
    "To Hit (2)",
    "Not Yet Dead",
    "Fog",
    "Escape Artist",
]

type AssaultSpecial = Literal[
    "Extra Damage",
    "Improved Extra Damage",
    "Cunning Assault",
    "Cunning Deflection",
    "Damage on Deflect",
    "Overrun",
    "Counter Attack",
    "Bonus",
    "Improvement",
    "Ork Reroll",    
    "Penalty",
    "Angle",
    "Troll Stench",
    "Fear",
    "Pre-Assault Retreat",
    "Retreat",
    "Disconnected",
    "FlyBy",
    "Lands",    

]

type ModelType = Literal[
    "Elite",
    "SuperElite",
    "Bio",
    "Bio Crew",
    "Crew",
    "Mechanical",
    "Illusion",
    "Infantry",
    "Cavalry",
    "Vehicle",
    "Motorcycle",
    "Helicopter",
    "Zeppelin",
    "Steampowerarmor",
    "Walking",
    "Floating",
    "Flying",
    "Tracked",
    "Wheeled",
    "Scout",
    "Elk",
    "Frog",
    "Drone",
    "Carrier",
    "Towed",
    "Monster",
    "Tinkerer",
    "Brother in Arms",
    "Roboprosthetic",
    "Amphibian",
    "Engineer",
    "Grunt",
    "Medic",
    "Officer"
]


class Cost(StrictModel):
    mp: int = 0
    cp: int = 0
    xp: int = 0
    ip: int = 0

    def __add__(self, other: Self) -> Self:
        """Return element-wise sum of two costs."""
        return self.__class__(
            mp=self.mp + other.mp,
            cp=self.cp + other.cp,
            xp=self.xp + other.xp,
            ip=self.ip + other.ip,
        )

    def __radd__(self, other: Self) -> Self:
        """Support sum(costs, Cost())."""
        return other.__add__(self)

    def __mul__(self, n: int) -> Self:
        """Return cost scaled by n."""
        return self.__class__(
            mp=self.mp * n, cp=self.cp * n, xp=self.xp * n, ip=self.ip * n
        )

    def __rmul__(self, n: int) -> Self:
        """Return cost scaled by n (reflected)."""
        return self.__mul__(n)

    def to_points(self) -> int:
        """Return the points value: mp + cp + xp + 3 * ip."""
        return self.mp + self.cp + self.xp + 3 * self.ip

    def __str__(self) -> str:
        """Return a human-readable cost string, graying out zero values."""

        def _part(value: int, unit: str) -> str:
            s = f"{value:2d}{unit}"
            return f"[gray30]{s}[/]" if value == 0 else s

        parts = [
            _part(self.mp, "mp"),
            _part(self.cp, "cp"),
            _part(self.xp, "xp"),
            _part(self.ip, "ip"),
        ]
        return " ".join(parts)


class EquipmentLimit(StrictModel):
    holder: EquipmentHolder
    limit: int


def _parse_equipment_limit(equipment_limit: str) -> EquipmentLimit:
    """Parse an equipment limit string into a model."""
    holder, _, number = equipment_limit.partition(":")
    limit = 999 if number == "∞" else int(number)
    return EquipmentLimit(holder=cast("EquipmentHolder", holder), limit=limit)


type ParsedEquipmentLimit = Annotated[
    EquipmentLimit, BeforeValidator(_parse_equipment_limit)
]


class Requirement(StrictModel):
    key: EquipmentHolder | Literal["type"]
    value: int | ModelType


def _parse_requirement(requirement: str) -> Requirement:
    """Parse a requirement string into a model."""
    key, _, value_or_type = requirement.partition(":")
    if key == "type":
        return Requirement(key="type", value=cast("ModelType", value_or_type))

    return Requirement(key=cast("EquipmentHolder", key), value=int(value_or_type))


type ParsedRequirement = Annotated[Requirement, BeforeValidator(_parse_requirement)]
