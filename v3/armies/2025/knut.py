"""Create Knut's 2025 army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("gnome")

army = ArmyList("gnome", "Knut's Assault Bots", [])

# 3 Balista_tractor
army = (
    army.add_unit("ballista_tractor_mark_i", race_config=cfg)
    .duplicate_unit(("ballista_tractor_mark_i", 0))
    .duplicate_unit(("ballista_tractor_mark_i", 0))
)


# x4 Mortars
army = (
    army.add_unit("gnome_infantry", race_config=cfg, nick="Mortar")
    .upgrade_unit(
        ("gnome_infantry", 0),
        model_key=("gnome_infantry", 0),
        upgrade_model_name="gnome_tinkerer",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("gnome_infantry", 0), equipment_name="assault_bot_mortar", race_config=cfg
    )
    .upgrade_model(
        ("gnome_infantry", 0),
        equipment_name="green_gas_launcher",
        model_key=("gnome_tinkerer", 0),
        race_config=cfg,
    )
    .duplicate_unit(("gnome_infantry", 0))
    .duplicate_unit(("gnome_infantry", 0))
    .duplicate_unit(("gnome_infantry", 0))
)

# x1 Death Ray tinkerer with Mechanical owl
army = (
    army.add_unit("gnome_infantry", race_config=cfg, nick="Death Ray with Owl")
    .upgrade_unit(
        ("gnome_infantry", 0),
        model_key=("gnome_infantry", 0),
        upgrade_model_name="gnome_tinkerer",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("gnome_infantry", 0), equipment_name="mechanical_owl", race_config=cfg
    )
    .upgrade_model(
        ("gnome_infantry", 0),
        equipment_name="experimental_death_ray",
        model_key=("gnome_tinkerer", 0),
        race_config=cfg,
    )
)

# x1 Death Ray tinkerer
army = (
    army.add_unit("gnome_infantry", race_config=cfg, nick="Death Ray Tinkerer")
    .upgrade_unit(
        ("gnome_infantry", 0),
        model_key=("gnome_infantry", 0),
        upgrade_model_name="gnome_tinkerer",
        race_config=cfg,
    )
    .upgrade_model(
        ("gnome_infantry", 0),
        equipment_name="experimental_death_ray",
        model_key=("gnome_tinkerer", 0),
        race_config=cfg,
    )
)

# Save the army to disk
io.save_army(army, army_name="2025/knut")

# Show the army in the console
io.print_army(army.resolve(cfg))
