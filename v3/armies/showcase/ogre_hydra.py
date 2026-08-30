"""Create a showcase Ogre army built around a single Ogre Hydra."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("ogre")

army = ArmyList("ogre", "Showcase Ogre Hydra", [])

# 1x Ogre Hydra
army = army.add_unit("ogre_hydra", race_config=cfg)

# 5x Ogre Infantry with Fancy Arquebus
army = (
    army.add_unit("ogre_infantry", race_config=cfg)
    .upgrade_all_models(
        ("ogre_infantry", 0), equipment_name="fancy_arquebus", race_config=cfg
    )
    .duplicate_unit(("ogre_infantry", 0))
    .duplicate_unit(("ogre_infantry", 0))
    .duplicate_unit(("ogre_infantry", 0))
    .duplicate_unit(("ogre_infantry", 0))
)

# 1x Ogre Robot
army = army.add_unit("ogre_robot", race_config=cfg)

# 3x Main Engine
army = army.add_unit("main_engine", race_config=cfg)

army = army.add_unit("artillery_wagon", race_config=cfg).duplicate_unit(
    ("artillery_wagon", 0)
)

# Save the army to disk
io.save_army(army, army_name="showcase/ogre_hydra")

# Show the army in the console
io.print_army(army.resolve(cfg))
