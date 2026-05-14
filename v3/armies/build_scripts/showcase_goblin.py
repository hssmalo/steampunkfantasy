"""Create a showcase Goblin army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("goblin")

army = ArmyList("goblin", "Showcase Goblin", ())

# 4x Elite Goblin Infantry w Grenadier, Gear bow, Acid Grenade
army = (
    army.add_unit("goblin_infantry", cfg)
    .upgrade_full_unit(("goblin_infantry", 0), "elite_goblin_infantry", cfg)
    .upgrade_all_models(("goblin_infantry", 0), "grenadier", cfg)
    .upgrade_all_models(("goblin_infantry", 0), "acid_grenade", cfg)
    .upgrade_all_models(("goblin_infantry", 0), "gear_bow", cfg)
    .duplicate_unit(("goblin_infantry", 0))
    .duplicate_unit(("goblin_infantry", 0))
    .duplicate_unit(("goblin_infantry", 0))
)

# 2x Goblin Infantry w Poison bow
army = (
    army.add_unit("goblin_infantry", cfg)
    .upgrade_all_models(("goblin_infantry", 4), "poison_bow", cfg)
    .duplicate_unit(("goblin_infantry", 4))
)

# 6x Goblin Infantry
army = (
    army.add_unit("goblin_infantry", cfg)
    .duplicate_unit(("goblin_infantry", 6))
    .duplicate_unit(("goblin_infantry", 6))
    .duplicate_unit(("goblin_infantry", 6))
    .duplicate_unit(("goblin_infantry", 6))
    .duplicate_unit(("goblin_infantry", 6))
)

# 4x Goblin Infantry Carrier
army = (
    army.add_unit("goblin_infantry_carrier", cfg)
    .duplicate_unit(("goblin_infantry_carrier", 0))
    .duplicate_unit(("goblin_infantry_carrier", 0))
    .duplicate_unit(("goblin_infantry_carrier", 0))
)

# 1x Heavy Carrier
army = army.add_unit("heavy_carrier", cfg)

# Save the army to disk
io.save_army(army, "showcase/goblin")

# Show the army in the console
io.print_army(army.resolve(cfg))
