"""Create a showcase Ogre army of scouts, infantry and Main Engines."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("ogre")

army = ArmyList("ogre", "Showcase Ogre Gunline", [])

# 6x Ogre Assault Scout with Fancy Arquebus
army = (
    army.add_unit("ogre_assault_scout", race_config=cfg)
    .upgrade_all_models(
        ("ogre_assault_scout", 0), equipment_name="fancy_arquebus", race_config=cfg
    )
    .duplicate_unit(("ogre_assault_scout", 0))
    .duplicate_unit(("ogre_assault_scout", 0))
    .duplicate_unit(("ogre_assault_scout", 0))
    .duplicate_unit(("ogre_assault_scout", 0))
    .duplicate_unit(("ogre_assault_scout", 0))
)

# 3x Ogre Infantry
army = (
    army.add_unit("ogre_infantry", race_config=cfg)
    .duplicate_unit(("ogre_infantry", 0))
    .duplicate_unit(("ogre_infantry", 0))
)

# 3x Main Engine
army = (
    army.add_unit("main_engine", race_config=cfg)
    .duplicate_unit(("main_engine", 0))
    .duplicate_unit(("main_engine", 0))
)

# Save the army to disk
io.save_army(army, army_name="showcase/ogre_gunline")

# Show the army in the console
io.print_army(army.resolve(cfg))
