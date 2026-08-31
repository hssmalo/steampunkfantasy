"""Create Morten's 2024 army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("gnome")

army = ArmyList("gnome", "Morten's Helicopter Assault", [])

# x1 Gnome Helicopter
army = (
    army.add_unit("gnome_helicopter", race_config=cfg)
    .duplicate_unit(("gnome_helicopter", 0))
    .duplicate_unit(("gnome_helicopter", 0))
    .duplicate_unit(("gnome_helicopter", 0))
)

# x1 Green Hell Riders: one Quad Bike upgraded to Tinkerer, who alone carries
# the Green Gas Launcher
army = (
    army.add_unit("quad_bike", race_config=cfg, nick="Green Hell Riders")
    .upgrade_unit(
        ("quad_bike", 0),
        model_key=("quad_bike", 0),
        upgrade_model_name="quadbike_tinkerer",
        race_config=cfg,
    )
    .upgrade_model(
        ("quad_bike", 0),
        model_key=("quadbike_tinkerer", 0),
        equipment_name="green_gas_launcher",
        race_config=cfg,
    )
).duplicate_unit(("quad_bike", 0))

# x1 PlasmaShield Riders: every model carries the Plasma Shield Generator
army = (
    army.add_unit("quad_bike", race_config=cfg, nick="PlasmaShield Riders")
    .upgrade_unit(
        ("quad_bike", 2),
        model_key=("quad_bike", 0),
        upgrade_model_name="quadbike_tinkerer",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("quad_bike", 2),
        equipment_name="plasma_shield_generator",
        race_config=cfg,
    )
    .duplicate_unit(("quad_bike", 2))
)


# x1 Gnome Infantry with Assault Bot Mortar
army = (
    army.add_unit("gnome_infantry", race_config=cfg)
    .upgrade_all_models(
        ("gnome_infantry", 0), equipment_name="assault_bot_mortar", race_config=cfg
    )
    .duplicate_unit(("gnome_infantry", 0))
)

# x1 Assault Bots
army = army.add_unit("assault_bots", race_config=cfg)
# .duplicate_unit(("assault_bots", 0))

# x1 Mechanical Rat
army = army.add_unit("mechanical_rat", race_config=cfg)
# .duplicate_unit(("mechanical_rat", 0))

# Save the army to disk
io.save_army(army, army_name="2024/morten")

# Show the army in the console
io.print_army(army.resolve(cfg))
