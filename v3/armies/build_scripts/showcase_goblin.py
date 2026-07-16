"""Create a showcase Goblin army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("goblin")

army = ArmyList("goblin", "Showcase Goblin", [])

# 4x Elite Goblin Infantry w Grenadier, Gear bow, Acid Grenade
army = (
    army.add_unit("goblin_infantry", race_config=cfg)
    .upgrade_full_unit(
        ("goblin_infantry", 0),
        upgrade_model_name="elite_goblin_infantry",
        race_config=cfg,
    )
    .upgrade_all_models(
        ("goblin_infantry", 0), equipment_name="grenadier", race_config=cfg
    )
    .upgrade_all_models(
        ("goblin_infantry", 0), equipment_name="acid_grenade", race_config=cfg
    )
    .upgrade_all_models(
        ("goblin_infantry", 0), equipment_name="gear_bow", race_config=cfg
    )
    .duplicate_unit(("goblin_infantry", 0))
    .duplicate_unit(("goblin_infantry", 0))
    .duplicate_unit(("goblin_infantry", 0))
)

# 2x Goblin Infantry w Poison bow
army = (
    army.add_unit("goblin_infantry", race_config=cfg)
    .upgrade_all_models(
        ("goblin_infantry", 4), equipment_name="poison_bow", race_config=cfg
    )
    .duplicate_unit(("goblin_infantry", 4))
)

# 6x Goblin Infantry
army = (
    army.add_unit("goblin_infantry", race_config=cfg)
    .duplicate_unit(("goblin_infantry", 6))
    .duplicate_unit(("goblin_infantry", 6))
    .duplicate_unit(("goblin_infantry", 6))
    .duplicate_unit(("goblin_infantry", 6))
    .duplicate_unit(("goblin_infantry", 6))
)

# 4x Goblin Infantry Carrier
army = (
    army.add_unit("goblin_infantry_carrier", race_config=cfg)
    .duplicate_unit(("goblin_infantry_carrier", 0))
    .duplicate_unit(("goblin_infantry_carrier", 0))
    .duplicate_unit(("goblin_infantry_carrier", 0))
)

# 1x Heavy Carrier
army = army.add_unit("heavy_carrier", race_config=cfg)

# Save the army to disk
io.save_army(army, army_name="showcase/goblin")

# Show the army in the console
io.print_army(army.resolve(cfg))
