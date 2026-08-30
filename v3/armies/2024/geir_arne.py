"""Create Geir Arne's 2024 army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("elf")

army = ArmyList("elf", "Geir Arne's Super Cavalry", [])

# x1 Tattoo Ink
army = army.add_unit("tattoo_ink", race_config=cfg)
# .duplicate_unit(("tattoo_ink", 0))

# x1 Armored Unicorn Rider
army = army.add_unit("armored_unicorn_rider", race_config=cfg)
# .duplicate_unit(("armored_unicorn_rider", 0))

# x1 Pegasus Rider
army = army.add_unit("pegasus_rider", race_config=cfg)
# .duplicate_unit(("pegasus_rider", 0))

# x1 Pachycephalosaurus Riders
army = army.add_unit("pachycephalosaurus_riders", race_config=cfg)
# .duplicate_unit(("pachycephalosaurus_riders", 0))

# x1 Elf Infantry
army = army.add_unit("elf_infantry", race_config=cfg)
# .duplicate_unit(("elf_infantry", 0))

# Save the army to disk
io.save_army(army, army_name="2024/geir_arne")

# Show the army in the console
io.print_army(army.resolve(cfg))
