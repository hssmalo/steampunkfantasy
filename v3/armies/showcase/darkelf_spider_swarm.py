"""Create a showcase Dark Elf army swarming with Mechanical Assault Spiders."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("darkelf")

army = ArmyList("darkelf", "Showcase Dark Elf Spider Swarm", [])

# 6x Roboprosthetic Dark Elf with SMG and Hide
army = (
    army.add_unit("roboprosthetic_darkelf", race_config=cfg)
    .upgrade_all_models(
        ("roboprosthetic_darkelf", 0), equipment_name="smg", race_config=cfg
    )
    .upgrade_all_models(
        ("roboprosthetic_darkelf", 0), equipment_name="hide", race_config=cfg
    )
    .duplicate_unit(("roboprosthetic_darkelf", 0))
    .duplicate_unit(("roboprosthetic_darkelf", 0))
    .duplicate_unit(("roboprosthetic_darkelf", 0))
    .duplicate_unit(("roboprosthetic_darkelf", 0))
    .duplicate_unit(("roboprosthetic_darkelf", 0))
)

# 6x Mechanical Assault Spider
army = (
    army.add_unit("mechanical_assault_spider", race_config=cfg)
    .duplicate_unit(("mechanical_assault_spider", 0))
    .duplicate_unit(("mechanical_assault_spider", 0))
    .duplicate_unit(("mechanical_assault_spider", 0))
    .duplicate_unit(("mechanical_assault_spider", 0))
    .duplicate_unit(("mechanical_assault_spider", 0))
)

# Save the army to disk
io.save_army(army, army_name="showcase/darkelf_spider_swarm")

# Show the army in the console
io.print_army(army.resolve(cfg))
