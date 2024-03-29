import data

ork = data.Race.from_toml("ork")
darkelf = data.Race.from_toml("darkelf")
dwarf = data.Race.from_toml("dwarf")
gnome= data.Race.from_toml("gnome")

hss = data.Team("Hss den store")
t = data.Team("Geir Arnes superorker")
t.add_unit(ork.units.grunt, name="Hans Sverre")
t.add_equipment("Hans Sverre", ork.equipments.clockwork_wings)
t.add_unit(ork.units.grunt)
t.add_unit(ork.units.grunt)
t.add_unit(ork.units.grunt)
t.add_unit(ork.units.bioengineered_ork, name="Geir Arne")
t.upgrade_model("Geir Arne", ork.models.elite_bioengineered_ork)
t.upgrade_model("Geir Arne", ork.models.elite_bioengineered_ork)
t.upgrade_model("Geir Arne", ork.models.elite_bioengineered_ork)
t.upgrade_model("Geir Arne", ork.models.elite_bioengineered_ork)
t.add_equipment("Geir Arne", ork.equipments.flame_covered_axe)
t.add_equipment("Geir Arne", ork.equipments.flame_covered_axe)
t.add_equipment("Geir Arne", ork.equipments.flame_covered_axe)
t.add_equipment("Geir Arne", ork.equipments.flame_covered_axe)
beo_1 = t.add_unit(ork.units.bioengineered_ork)
t.upgrade_model(beo_1, ork.models.elite_bioengineered_ork)
t.upgrade_model(beo_1, ork.models.elite_bioengineered_ork)
t.upgrade_model(beo_1, ork.models.elite_bioengineered_ork)
t.upgrade_model(beo_1, ork.models.elite_bioengineered_ork)
t.add_equipment(beo_1, ork.equipments.flame_covered_axe)
t.add_equipment(beo_1, ork.equipments.flame_covered_axe)
t.add_equipment(beo_1, ork.equipments.flame_covered_axe)
t.add_equipment(beo_1, ork.equipments.flame_covered_axe)
beo_2 = t.add_unit(ork.units.bioengineered_ork)
t.upgrade_model(beo_2, ork.models.elite_bioengineered_ork)
t.upgrade_model(beo_2, ork.models.elite_bioengineered_ork)
t.upgrade_model(beo_2, ork.models.elite_bioengineered_ork)
t.upgrade_model(beo_2, ork.models.elite_bioengineered_ork)
beo_3 = t.add_unit(ork.units.bioengineered_ork)
t.upgrade_model(beo_3, ork.models.elite_bioengineered_ork)
t.upgrade_model(beo_3, ork.models.elite_bioengineered_ork)
t.upgrade_model(beo_3, ork.models.elite_bioengineered_ork)
t.upgrade_model(beo_3, ork.models.elite_bioengineered_ork)


m = data.Team("Default DarkElf")
m.add_unit(darkelf.units.mechanical_assault_spider)
cav = m.add_unit(darkelf.units.elite_mechanical_cavalry, name = 'Mechanical Cavalry with Imp')
m.add_equipment(cav, darkelf.equipments.mechanical_imp)
m.add_unit(darkelf.units.darkelf_infantry)


g = data.Team("Default Gnome")
g.add_unit(gnome.units.gnome_helicopter)
inf = g.add_unit(gnome.units.gnome_infantry, name = 'PlasmaShield Infantry')
g.add_equipment(inf, gnome.equipments.plasma_shield_generator)
g.add_unit(gnome.units.gnome_motorcycle)



d = data.Team("Default Dwarf")
d.add_unit(dwarf.units.gunblasterwagon)
inf = d.add_unit(dwarf.units.dwarf_infantry)
d.add_equipment(inf, dwarf.equipments.heavy_musket)
d.add_equipment(inf, dwarf.equipments.wheeled_shieldwall)
d.add_unit(dwarf.units.tamed_balrog)


import IPython; IPython.embed()
