"""Create a showcase Gnome army built around Ballista Tractors."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("gnome")

army = ArmyList("gnome", "Showcase Gnome Ballista Battery", [])

# 6x Gnome Motorcycle
army = (
    army.add_unit("gnome_motorcycle", race_config=cfg)
    .duplicate_unit(("gnome_motorcycle", 0))
    .duplicate_unit(("gnome_motorcycle", 0))
    .duplicate_unit(("gnome_motorcycle", 0))
    .duplicate_unit(("gnome_motorcycle", 0))
    .duplicate_unit(("gnome_motorcycle", 0))
)

# 3x Gnome Infantry
army = (
    army.add_unit("gnome_infantry", race_config=cfg)
    .duplicate_unit(("gnome_infantry", 0))
    .duplicate_unit(("gnome_infantry", 0))
)

# 3x Ballista Tractor, Mark I
army = (
    army.add_unit("ballista_tractor_mark_i", race_config=cfg)
    .duplicate_unit(("ballista_tractor_mark_i", 0))
    .duplicate_unit(("ballista_tractor_mark_i", 0))
)

# Save the army to disk
io.save_army(army, army_name="showcase/gnome_ballista_battery")

# Show the army in the console
io.print_army(army.resolve(cfg))
