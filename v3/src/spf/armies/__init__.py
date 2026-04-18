"""Army data structures, builders, and IO for SteamPunkFantasy.

Public API (resolved tier — no race_config needed after construction):
  Army, Unit, Model — import directly from here

Build-time tier — for constructing armies in code:
  ArmyList, ArmyUnit, ArmyModel — import from spf.armies.build
"""

from spf.armies.army import Army
from spf.armies.build import (
    ArmyList,
    available_equipment,
    available_models,
    validate_army,
)
from spf.armies.model import Model
from spf.armies.unit import Unit

__all__ = [
    "Army",
    "ArmyList",
    "Model",
    "Unit",
    "available_equipment",
    "available_models",
    "validate_army",
]
