"""Create a showcase Goblin army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("elf")

army = ArmyList("elf", "Showcase Elf", [])

# x2 Elf Infantry
army = army.add_unit("elf_infantry", race_config=cfg).duplicate_unit(
    ("elf_infantry", 0)
)

# 4x Oliphant
army = (
    army.add_unit("armored_oliphant_riders", race_config=cfg)
    .duplicate_unit(("armored_oliphant_riders", 0))
    .duplicate_unit(("armored_oliphant_riders", 0))
    .duplicate_unit(("armored_oliphant_riders", 0))
)

# x2 E34
army = army.add_unit("e34", race_config=cfg).duplicate_unit(("e34", 0))


# Save the army to disk
io.save_army(army, army_name="showcase/elf")

# Show the army in the console
io.print_army(army.resolve(cfg))
