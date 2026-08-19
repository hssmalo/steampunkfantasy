"""Create Geir Arne's 2025 army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("ork")

army = ArmyList("ork", "Geir Arne's Sabeltann Fighters", [])

# 2x Ork Char B1
army = army.add_unit("ork_char_b1", race_config=cfg).duplicate_unit(("ork_char_b1", 0))

# 2x Elite Infantry with Power Spear and Wings
army = (
    army.add_unit("ork_infantry", race_config=cfg)
    .upgrade_unit(
        ("ork_infantry", 0),
        model_key=("ork_infantry", 0),
        upgrade_model_name="elite_ork_infantry",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("ork_infantry", 0), equipment_name="clockwork_power_spear", race_config=cfg
    )
    .upgrade_all_models(
        ("ork_infantry", 0), equipment_name="clockwork_wings", race_config=cfg
    )
    .duplicate_unit(("ork_infantry", 0))
)

# Add champion to one Elite infantry
army = (
    army.add_unit("champion", race_config=cfg)
    .upgrade_all_models(
        ("champion", 0), equipment_name="clockwork_power_spear", race_config=cfg
    )
    .upgrade_all_models(
        ("champion", 0), equipment_name="clockwork_wings", race_config=cfg
    )
)


# 2x Bioengineered Ork
army = (
    army.add_unit("bioengineered_ork", race_config=cfg)
    .upgrade_all_models(
        ("bioengineered_ork", 0), equipment_name="ork_pistol", race_config=cfg
    )
    .upgrade_all_models(
        ("bioengineered_ork", 0), equipment_name="ork_pistol", race_config=cfg
    )
    .upgrade_all_models(
        ("bioengineered_ork", 0), equipment_name="ork_pistol", race_config=cfg
    )
    .upgrade_all_models(
        ("bioengineered_ork", 0), equipment_name="ork_pistol", race_config=cfg
    )
    .duplicate_unit(("bioengineered_ork", 0))
)

# 3x Warg Rider
army = (
    army.add_unit("warg_rider", race_config=cfg)
    .duplicate_unit(("warg_rider", 0))
    .duplicate_unit(("warg_rider", 0))
)

# 1x Grunt
army = army.add_unit("grunt", race_config=cfg)

# Save the army to disk
io.save_army(army, army_name="2025/geir_arne")

# Show the army in the console
io.print_army(army.resolve(cfg))
