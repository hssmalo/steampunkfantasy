"""Create a showcase Ork army of grunts, Warg Riders and Speedheads."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("ork")

army = ArmyList("ork", "Showcase Ork Warband", [])

# 6x Grunt
army = (
    army.add_unit("grunt", race_config=cfg)
    .duplicate_unit(("grunt", 0))
    .duplicate_unit(("grunt", 0))
    .duplicate_unit(("grunt", 0))
    .duplicate_unit(("grunt", 0))
    .duplicate_unit(("grunt", 0))
)

# 6x Warg Rider with Flame-covered-axe
army = (
    army.add_unit("warg_rider", race_config=cfg)
    .upgrade_all_models(
        ("warg_rider", 0), equipment_name="flame_covered_axe", race_config=cfg
    )
    .duplicate_unit(("warg_rider", 0))
    .duplicate_unit(("warg_rider", 0))
    .duplicate_unit(("warg_rider", 0))
    .duplicate_unit(("warg_rider", 0))
    .duplicate_unit(("warg_rider", 0))
)

# 4x Speedhead
army = (
    army.add_unit("speedhead", race_config=cfg)
    .duplicate_unit(("speedhead", 0))
    .duplicate_unit(("speedhead", 0))
    .duplicate_unit(("speedhead", 0))
)

# Save the army to disk
io.save_army(army, army_name="showcase/ork_warband")

# Show the army in the console
io.print_army(army.resolve(cfg))
