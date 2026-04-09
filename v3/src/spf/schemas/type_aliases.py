"""Type aliases for SteamPunkFantasy."""

from typing import Annotated, Literal, cast

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
    "Forward Position",
    "Regeneration",
    "Take Cover",
    "Fire Order",
    "Evation",
    "Chase",
    "Transport",
    "Tow",
    "Resistance",
    "Immunity",
    "Repair",
    "Heal",
    "Heal (2)",
    "Repairing",
    "Suicide",
    "LoS",
    "Terror",
    "Poison Cloud",
    "Fog",
    "Movement",
    "Pet",
    "Improved Resistance",
    "Improved Resistance (2)"
]
type ModelSpecial = Literal[
    "To Hit",
    "To Hit (2)",
    "Not Yet Dead",
    
    
]

type AssaultSpecial = Literal[
    "Cunning Assault",
    "Fear",
    "Troll Stench",
    "Ork Reroll",
    "Angle",
    "Pre-Assault Retreat",
    "Damage",
    "Damage on Deflect"
]
    
type ModelType = Literal[
    "Elite",
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
]


class Cost(StrictModel):
    mp: int = 0
    cp: int = 0
    xp: int = 0
    ip: int = 0


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
