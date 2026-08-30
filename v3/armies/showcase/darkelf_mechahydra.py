"""Create a showcase Dark Elf army of infantry, scouts and two MechaHydras."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("darkelf")

army = ArmyList("darkelf", "Showcase Dark Elf MechaHydra", [])

# 3x Scout with Mechanical Imp
army = (
    army.add_unit("scout", race_config=cfg)
    .upgrade_all_models(("scout", 0), equipment_name="mechanical_imp", race_config=cfg)
    .duplicate_unit(("scout", 0))
    .duplicate_unit(("scout", 0))
)

# 3x Dark Elf Infantry with Mechanical Imp and Hide
army = (
    army.add_unit("darkelf_infantry", race_config=cfg)
    .upgrade_all_models(
        ("darkelf_infantry", 0), equipment_name="mechanical_imp", race_config=cfg
    )
    .upgrade_all_models(("darkelf_infantry", 0), equipment_name="hide", race_config=cfg)
    .duplicate_unit(("darkelf_infantry", 0))
    .duplicate_unit(("darkelf_infantry", 0))
)

# 2x MechaHydra
army = army.add_unit("mechahydra", race_config=cfg).duplicate_unit(("mechahydra", 0))

# Save the army to disk
io.save_army(army, army_name="showcase/darkelf_mechahydra")

# Show the army in the console
io.print_army(army.resolve(cfg))
