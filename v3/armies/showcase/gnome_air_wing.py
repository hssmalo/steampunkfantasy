"""Create a showcase Gnome army built around Gnome Helicopters."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("gnome")

army = ArmyList("gnome", "Showcase Gnome Air Wing", [])

# 4x Gnome Motorcycle
army = (
    army.add_unit("gnome_motorcycle", race_config=cfg)
    .duplicate_unit(("gnome_motorcycle", 0))
    .duplicate_unit(("gnome_motorcycle", 0))
    .duplicate_unit(("gnome_motorcycle", 0))
)

# 4x Gnome Infantry with Acid Splash
army = (
    army.add_unit("gnome_infantry", race_config=cfg)
    .upgrade_all_models(
        ("gnome_infantry", 0), equipment_name="acid_splash", race_config=cfg
    )
    .duplicate_unit(("gnome_infantry", 0))
    .duplicate_unit(("gnome_infantry", 0))
    .duplicate_unit(("gnome_infantry", 0))
)

# 4x Gnome Helicopter
army = (
    army.add_unit("gnome_helicopter", race_config=cfg)
    .duplicate_unit(("gnome_helicopter", 0))
    .duplicate_unit(("gnome_helicopter", 0))
    .duplicate_unit(("gnome_helicopter", 0))
)

# Save the army to disk
io.save_army(army, army_name="showcase/gnome_air_wing")

# Show the army in the console
io.print_army(army.resolve(cfg))
