"""Create a showcase Ork army built around two Ork Char B1 tanks."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("ork")

army = ArmyList("ork", "Showcase Ork Armored Fist", [])

# 4x Grunt
army = (
    army.add_unit("grunt", race_config=cfg)
    .duplicate_unit(("grunt", 0))
    .duplicate_unit(("grunt", 0))
    .duplicate_unit(("grunt", 0))
)

# 4x BioEngineered Ork with Clockwork Power Spear and Pyro
army = (
    army.add_unit("bioengineered_ork", race_config=cfg)
    .upgrade_all_models(
        ("bioengineered_ork", 0),
        equipment_name="clockwork_power_spear",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("bioengineered_ork", 0), equipment_name="pyro", race_config=cfg
    )
    .duplicate_unit(("bioengineered_ork", 0))
    .duplicate_unit(("bioengineered_ork", 0))
    .duplicate_unit(("bioengineered_ork", 0))
)

# 2x Ork Char B1
army = army.add_unit("ork_char_b1", race_config=cfg).duplicate_unit(("ork_char_b1", 0))

# Save the army to disk
io.save_army(army, army_name="showcase/ork_armored_fist")

# Show the army in the console
io.print_army(army.resolve(cfg))
