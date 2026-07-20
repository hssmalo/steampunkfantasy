"""Create a showcase Goblin army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("dwarf")

army = ArmyList("dwarf", "Showcase Dwarf", [])

# x6 Dwarf Infantry
army = (
    army.add_unit("dwarf_infantry", race_config=cfg)
    .upgrade_full_unit(
        ("dwarf_infantry", 0),
        upgrade_model_name="elite_dwarf_infantry",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("dwarf_infantry", 0), equipment_name="blast_sticks", race_config=cfg
    )
    .upgrade_all_models(
        ("dwarf_infantry", 0), equipment_name="vest_of_life_support", race_config=cfg
    )
    .upgrade_all_models(
        ("dwarf_infantry", 0),
        equipment_name="trench_coat_of_resistance",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("dwarf_infantry", 0), equipment_name="industrial_small_arms_production", race_config=cfg
    )
    .duplicate_unit(("dwarf_infantry", 0))
    .duplicate_unit(("dwarf_infantry", 0))
    .duplicate_unit(("dwarf_infantry", 0))
    .duplicate_unit(("dwarf_infantry", 0))
    .duplicate_unit(("dwarf_infantry", 0))
)

# 3x Transport Zeppelin
army = (
    (army.add_unit("transport_zeppelin", race_config=cfg))
    .duplicate_unit(("transport_zeppelin", 0))
    .duplicate_unit(("transport_zeppelin", 0))
)

# x3 GunBlasterWagon
army = (
    army.add_unit("gunblasterwagon", race_config=cfg)
    .duplicate_unit(("gunblasterwagon", 0))
    .duplicate_unit(("gunblasterwagon", 0))
)


# Save the army to disk
io.save_army(army, army_name="2025/morten")

# Show the army in the console
io.print_army(army.resolve(cfg))
