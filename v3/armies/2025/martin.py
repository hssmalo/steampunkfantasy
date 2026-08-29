"""Create Martin's 2025 army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("darkelf")

army = ArmyList("darkelf", "Martin DarkElf", [])

# 1x Queen YY
army = army.add_unit("queen_yy", race_config=cfg)

# x2 Mechanical Scorpions
army = army.add_unit("mechanical_scorpion", race_config=cfg).duplicate_unit(
    ("mechanical_scorpion", 0)
)

# x2 Nightmare_mechanical_cavalry
army = army.add_unit("nightmare_mechanical_cavalry", race_config=cfg).duplicate_unit(
    ("nightmare_mechanical_cavalry", 0)
)


# 2x Roboprostetic Darkelf
army = (
    army.add_unit("roboprosthetic_darkelf", race_config=cfg)
    .upgrade_all_models(
        ("roboprosthetic_darkelf", 0), equipment_name="smg", race_config=cfg
    )
    .upgrade_all_models(
        ("roboprosthetic_darkelf", 0),
        equipment_name="integrated_pistol",
        race_config=cfg,
    )
    .duplicate_unit(("roboprosthetic_darkelf", 0))
)


# 2x Darkelf Infantry with smg and poison grenades
army = (
    army.add_unit("darkelf_infantry", race_config=cfg)
    .upgrade_all_models(("darkelf_infantry", 0), equipment_name="smg", race_config=cfg)
    .upgrade_all_models(
        ("darkelf_infantry", 0), equipment_name="poison_fog_grenade", race_config=cfg
    )
    .duplicate_unit(("darkelf_infantry", 0))
)


# Save the army to disk
io.save_army(army, army_name="2025/martin")

# Show the army in the console
io.print_army(army.resolve(cfg))
