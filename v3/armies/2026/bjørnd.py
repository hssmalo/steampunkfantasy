"""Create a showcase Goblin army."""

from spf import races
from spf.armies import ArmyList, io

cfg = races.get_race("goblin")

army = ArmyList("goblin", "Bjørns Goblin Grenadiers", [])

# 4x Elite Goblin Infantry w Grenadier, Gear bow, Acid Grenade
army = (
    army.add_unit("goblin_infantry", race_config=cfg, nick="Elite Goblin Grenadier")
    .upgrade_full_unit(
        ("goblin_infantry", 0),
        upgrade_model_name="elite_goblin_infantry",
        race_config=cfg,
    )
    .equip_unit(("goblin_infantry", 0), equipment_name="grenadier", race_config=cfg)
    .equip_unit(("goblin_infantry", 0), equipment_name="acid_grenade", race_config=cfg)
    .equip_unit(("goblin_infantry", 0), equipment_name="gear_bow", race_config=cfg)
    .duplicate_unit(("goblin_infantry", 0), nick="Elite Goblin Grenadier")
    .duplicate_unit(("goblin_infantry", 0), nick="Elite Goblin Grenadier")
    .duplicate_unit(("goblin_infantry", 0), nick="Elite Goblin Grenadier")
)

# 1x Goblin Infantry w Poison bow
army = army.add_unit(
    "goblin_infantry", race_config=cfg, nick="Goblin Infantry with Poison Bow"
).equip_unit(("goblin_infantry", 4), equipment_name="poison_bow", race_config=cfg)

# 2x Goblin Infantry w Ogre Rifle
army = (
    army.add_unit(
        "goblin_infantry", race_config=cfg, nick="Goblin Infantry with Ogre Rifle"
    ).equip_unit(("goblin_infantry", 5), equipment_name="ogre_rifle", race_config=cfg)
).duplicate_unit(("goblin_infantry", 5))

# 5x Goblin Infantry
army = (
    army.add_unit("goblin_infantry", race_config=cfg)
    .duplicate_unit(("goblin_infantry", 7))
    .duplicate_unit(("goblin_infantry", 7))
    .duplicate_unit(("goblin_infantry", 7))
    .duplicate_unit(("goblin_infantry", 7))
)

# 6x Goblin Infantry Carrier
army = (
    army.add_unit("modified_truck", race_config=cfg)
    .duplicate_unit(("modified_truck", 0))
    .duplicate_unit(("modified_truck", 0))
    .duplicate_unit(("modified_truck", 0))
    .duplicate_unit(("modified_truck", 0))
    .duplicate_unit(("modified_truck", 0))
)

# 2x Fire Birds
army = army.add_unit("mechanical_fire_bird", race_config=cfg).duplicate_unit(
    ("mechanical_fire_bird", 0)
)

# Save the army to disk
io.save_army(army, army_name="2026/bjørnd")

# Show the army in the console
io.print_army(army.resolve(cfg))
