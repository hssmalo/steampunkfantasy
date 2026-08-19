"""Create a showcase Goblin army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("dwarf")

army = ArmyList("dwarf", "Showcase Dwarf", [])

# x2 Dwarf Infantry
army = army.add_unit("dwarf_infantry", race_config=cfg).duplicate_unit(
    ("dwarf_infantry", 0)
)

# 4x SteampowerArmor
army = (
    army.add_unit("steampowerarmor", race_config=cfg)
    .upgrade_all_models(
        ("steampowerarmor", 0),
        equipment_name="multibarreled_heavy_musket",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("steampowerarmor", 0), equipment_name="vest_of_life_support", race_config=cfg
    )
    .duplicate_unit(("steampowerarmor", 0))
    .duplicate_unit(("steampowerarmor", 0))
    .duplicate_unit(("steampowerarmor", 0))
)

# 1x Tamed Balrog
army = army.add_unit("tamed_balrog", race_config=cfg)

# x2 Zap
army = army.add_unit("zap", race_config=cfg).duplicate_unit(("zap", 0))


# Save the army to disk
io.save_army(army, army_name="showcase/dwarf")

# Show the army in the console
io.print_army(army.resolve(cfg))
