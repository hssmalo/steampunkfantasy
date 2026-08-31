"""Create a showcase Goblin army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("gnome")

army = ArmyList("gnome", "Helicopters with Experimental Weapons", [])

# x4 Frost Ray Infantry
army = (
    army.add_unit("gnome_infantry", race_config=cfg, nick="Frost Ray Infantry")
    .upgrade_all_models(
        ("gnome_infantry", 0), equipment_name="frost_ray", race_config=cfg
    )
    .duplicate_unit(("gnome_infantry", 0), nick="Frost Ray Infantry")
    .duplicate_unit(("gnome_infantry", 0), nick="Frost Ray Infantry")
    .duplicate_unit(("gnome_infantry", 0), nick="Frost Ray Infantry")
)

army = army.add_unit("gnome_infantry", race_config=cfg).duplicate_unit(
    ("gnome_infantry", 4)
)


army = (
    army.add_unit("gnome_helicopter", race_config=cfg)
    .upgrade_unit(
        ("gnome_helicopter", 0),
        model_key=("gnome_helicopter", 0),
        upgrade_model_name="tinkerer_helicopter",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("gnome_helicopter", 0),
        equipment_name="experimental_guided_missile",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("gnome_helicopter", 0),
        equipment_name="helicopter_mounted_green_gas_launcher",
        race_config=cfg,
    )
    .duplicate_unit(("gnome_helicopter", 0))
    .duplicate_unit(("gnome_helicopter", 0))
    .duplicate_unit(("gnome_helicopter", 0))
)


# Save the army to disk
io.save_army(army, army_name="2026/gnome")

# Show the army in the console
io.print_army(army.resolve(cfg))
