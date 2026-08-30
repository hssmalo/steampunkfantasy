"""Create Ole Petter's 2024 army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("dwarf")

army = ArmyList("dwarf", "Ole Petter's SteamPowerArmor with Balrog Assault", [])

# x1 SteamPowerArmor with Vest of Life Support and MultiBarreled Heavy Musket
army = (
    army.add_unit("steampowerarmor", race_config=cfg)
    .upgrade_all_models(
        ("steampowerarmor", 0),
        equipment_name="vest_of_life_support",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("steampowerarmor", 0),
        equipment_name="multibarreled_heavy_musket",
        race_config=cfg,
    )
)
# .duplicate_unit(("steampowerarmor", 0))

# x1 Tamed Balrog
army = army.add_unit("tamed_balrog", race_config=cfg)
# .duplicate_unit(("tamed_balrog", 0))

# x1 Zap
army = army.add_unit("zap", race_config=cfg)
# .duplicate_unit(("zap", 0))

# x1 Dwarf Infantry
army = army.add_unit("dwarf_infantry", race_config=cfg)
# .duplicate_unit(("dwarf_infantry", 0))

# Save the army to disk
io.save_army(army, army_name="2024/ole_petter")

# Show the army in the console
io.print_army(army.resolve(cfg))
