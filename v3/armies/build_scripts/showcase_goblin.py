from spf.armies import army, build, io
from spf import races

goblin = races.get_race('goblin')

 showcase = build.ArmyList('goblin', 'Showcase Goblin', [])

i1 = build._make_default_army_unit('goblin_infantry', goblin)

i1 = i1.upgrade_unit(('goblin_infantry', 0), 'elite_goblin_infantry', goblin)
i1 = i1.upgrade_unit(('goblin_infantry', 0), 'elite_goblin_infantry', goblin)
i1 = i1.upgrade_unit(('goblin_infantry', 0), 'elite_goblin_infantry', goblin)
i1 = i1.upgrade_unit(('goblin_infantry', 0), 'elite_goblin_infantry', goblin)

i1 = i1.upgrade_model(('goblin_infantry', 0), 'grenadier', goblin)
i1 = i1.upgrade_model(('elite_goblin_infantry', 0), 'gear_bow', goblin)

showcase.units.append(i1)
showcase.units.append(i1)
showcase.units.append(i1)
showcase.units.append(i1)

i2 = build._make_default_army_unit('goblin_infantry', goblin)
i2 = i2.upgrade_model(('goblin_infantry', 0), 'poison_bow', goblin)

showcase.units.append(i2)
showcase.units.append(i2)

i3 = build._make_default_army_unit('goblin_infantry', goblin)

showcase.units.append(i3)
showcase.units.append(i3)
showcase.units.append(i3)
showcase.units.append(i3)
showcase.units.append(i3)
showcase.units.append(i3)

t1 = build._make_default_army_unit('goblin_infantry_carrier', goblin)

showcase.units.append(t1)
showcase.units.append(t1)
showcase.units.append(t1)
showcase.units.append(t1)

t2 = build._make_default_army_unit('heavy_carrier', goblin)

showcase.units.append(t2)

io.save_army(showcase, 'showcase_goblin')
