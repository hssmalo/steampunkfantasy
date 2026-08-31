"""Create a showcase Goblin army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("gnome")

army = ArmyList("gnome", "Showcase Gnome", [])

# 4x Gnome Assault Bot Mortar
army = (
    army.add_unit("gnome_infantry", race_config=cfg)
    .upgrade_unit(
        ("gnome_infantry", 0),
        model_key=("gnome_infantry", 0),
        upgrade_model_name="gnome_tinkerer",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("gnome_infantry", 0), equipment_name="assault_bot_mortar", race_config=cfg
    )
    .duplicate_unit(("gnome_infantry", 0))
    .duplicate_unit(("gnome_infantry", 0))
    .duplicate_unit(("gnome_infantry", 0))
)

# for now, add assault bots manually.
army = army.add_unit("assault_bots", race_config=cfg)


army = (
    army.add_unit("ballista_tractor_mark_i", race_config=cfg)
    .duplicate_unit(("ballista_tractor_mark_i", 0))
    .duplicate_unit(("ballista_tractor_mark_i", 0))
)

# Save the army to disk
io.save_army(army, army_name="showcase/gnome")

# Show the army in the console
io.print_army(army.resolve(cfg))
