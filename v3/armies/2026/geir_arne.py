"""Create Geir Arne's 2026 army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("ork")

army = ArmyList("ork", "Geir Arne's Pyro Slingers", [])

# 3x Battlewagon
army = (
    army.add_unit("battlewagon", race_config=cfg)
    .duplicate_unit(("battlewagon", 0))
    .duplicate_unit(("battlewagon", 0))
)

army = (
    army.add_unit("bioengineered_ork", race_config=cfg)
    .equip_unit(
        ("bioengineered_ork", 0), equipment_name="hand_catapult", race_config=cfg
    )
    .equip_unit(
        ("bioengineered_ork", 0), equipment_name="grenade_sling", race_config=cfg
    )
    .equip_unit(
        ("bioengineered_ork", 0), equipment_name="clockwork_monocular", race_config=cfg
    )
)

# 1x Werewarg
army = (
    army.add_unit("ork_werewarg", race_config=cfg)
    .equip_unit(("ork_werewarg", 0), equipment_name="pyro", race_config=cfg)
    .equip_unit(("ork_werewarg", 0), equipment_name="war_drum", race_config=cfg)
)

# 3x Warg Rider
army = (
    army.add_unit("warg_rider", race_config=cfg)
    # .duplicate_unit(("warg_rider", 0))
    # .duplicate_unit(("warg_rider", 0))
)

army = (
    army.add_unit("ork_infantry", race_config=cfg)
    .equip_unit(("ork_infantry", 0), equipment_name="ork_pistol", race_config=cfg)
    .equip_unit(("ork_infantry", 0), equipment_name="ork_pistol", race_config=cfg)
    .duplicate_unit(("ork_infantry", 0))
    .duplicate_unit(("ork_infantry", 0))
)

# 1x Grunt
army = army.add_unit("grunt", race_config=cfg).duplicate_unit(("grunt", 0))

# Save the army to disk
io.save_army(army, army_name="2026/geir_arne")

# Show the army in the console
io.print_army(army.resolve(cfg))
