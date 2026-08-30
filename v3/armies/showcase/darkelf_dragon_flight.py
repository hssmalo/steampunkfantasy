"""Create a showcase Dark Elf army led by a Mechanical Red Dragon."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("darkelf")

army = ArmyList("darkelf", "Showcase Dark Elf Dragon Flight", [])

# 6x Roboprosthetic Dark Elf with SMG
army = (
    army.add_unit("roboprosthetic_darkelf", race_config=cfg)
    .upgrade_all_models(
        ("roboprosthetic_darkelf", 0), equipment_name="smg", race_config=cfg
    )
    .duplicate_unit(("roboprosthetic_darkelf", 0))
    .duplicate_unit(("roboprosthetic_darkelf", 0))
    .duplicate_unit(("roboprosthetic_darkelf", 0))
    .duplicate_unit(("roboprosthetic_darkelf", 0))
    .duplicate_unit(("roboprosthetic_darkelf", 0))
)

# 1x Mechanical Red Dragon
army = army.add_unit("mechanical_red_dragon", race_config=cfg)

# Save the army to disk
io.save_army(army, army_name="showcase/darkelf_dragon_flight")

# Show the army in the console
io.print_army(army.resolve(cfg))
