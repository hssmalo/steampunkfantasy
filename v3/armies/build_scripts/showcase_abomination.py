"""Create a showcase Goblin army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("abomination")

army = ArmyList("abomination", "Showcase Abomination", [])

# x2 Abomination Infantry
army = (
    army.add_unit("abomination_infantry", race_config=cfg)
    .upgrade_all_models(
        ("abomination_infantry", 0),
        equipment_name="fog_grenade_mortar",
        race_config=cfg,
    )
    .duplicate_unit(("abomination_infantry", 0))
)

# 2x Forg Riders with frog armor
army = (
    army.add_unit("giant_frog_riders", race_config=cfg)
    .upgrade_all_models(
        ("giant_frog_riders", 0), equipment_name="frog_cavalry_armor", race_config=cfg
    )
    .upgrade_all_models(
        ("giant_frog_riders", 0),
        equipment_name="tentacle_cracklespears",
        race_config=cfg,
    )
    .duplicate_unit(("giant_frog_riders", 0))
    .duplicate_unit(("giant_frog_riders", 0))
    .duplicate_unit(("giant_frog_riders", 0))
)


# x4 squid
army = (
    army.add_unit("squid", race_config=cfg)
    .duplicate_unit(("squid", 0))
    .duplicate_unit(("squid", 0))
    .duplicate_unit(("squid", 0))
)


# x1 Horror
army = army.add_unit("horror", race_config=cfg)


# Save the army to disk
io.save_army(army, army_name="showcase/abomination")

# Show the army in the console
io.print_army(army.resolve(cfg))
