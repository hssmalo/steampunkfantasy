"""Create Knut's 2024 army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("ork")

army = ArmyList("ork", "Knut Sends the Trolls", [])

# x1 Troll
army = army.add_unit("troll", race_config=cfg)
# .duplicate_unit(("troll", 0))

# x1 Ork Infantry with Clockwork Power Spear
army = army.add_unit(
    "ork_infantry", race_config=cfg, nick="PowerSpear"
).upgrade_all_models(
    ("ork_infantry", 0), equipment_name="clockwork_power_spear", race_config=cfg
)
# .duplicate_unit(("ork_infantry", 0))

# x1 Ork Infantry with Grenade Sling
army = army.add_unit(
    "ork_infantry", race_config=cfg, nick="GrenadeSling"
).upgrade_all_models(
    ("ork_infantry", 1), equipment_name="grenade_sling", race_config=cfg
)
# .duplicate_unit(("ork_infantry", 1))

# x1 BattleWagon
army = army.add_unit("battlewagon", race_config=cfg)
# .duplicate_unit(("battlewagon", 0))

# x1 Crushing HammerHead
army = army.add_unit("hammerhead", race_config=cfg, nick="Crushing HammerHead")
# .duplicate_unit(("hammerhead", 0))

# x1 Grunt
army = army.add_unit("grunt", race_config=cfg)
# .duplicate_unit(("grunt", 0))

# Save the army to disk
io.save_army(army, army_name="2024/knut")

# Show the army in the console
io.print_army(army.resolve(cfg))
