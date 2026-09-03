
import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 

import data

darkelf = data.Race.from_toml("darkelf")


knut = data.Team("Knuts DarkElf")
knut.add_unit(darkelf.units.mechanical_assault_spider)
knut.add_unit(darkelf.units.queen_yy)
mortar = knut.add_unit(darkelf.units.assasin, name = 'Mortar Assasin')
knut.add_equipment(mortar, darkelf.equipments.mortar1a)
knut.add_equipment(mortar, darkelf.equipments.mechanical_imp)
crossbow = knut.add_unit(darkelf.units.darkelf_infantry, name = 'crossbow men')
knut.add_equipment(crossbow, darkelf.equipments.crossbow)
knut.add_equipment(crossbow, darkelf.equipments.hide)
knut.add_unit(darkelf.units.scout)

dwarf = data.Race.from_toml("dwarf")

bjorn = data.Team("Bjorns Dwarfs")
bjorn.add_unit(dwarf.units.zeppelin)
bjorn.add_unit(dwarf.units.dwarf_at_gun)
musketeer = bjorn.add_unit(dwarf.units.dwarf_infantry, name= 'Musketeers')
bjorn.upgrade_model('Musketeers', dwarf.models.elite_dwarf_infantry)
bjorn.upgrade_model('Musketeers', dwarf.models.elite_dwarf_infantry)
bjorn.add_equipment(musketeer, dwarf.equipments.enhanced_heavy_musket)
bjorn.add_unit(dwarf.units.dwarf_infantry)

gnome = data.Race.from_toml("gnome")

ole = data.Team("Oles Gnomes")

ole.add_unit(gnome.units.ballista_tractor_markI)

quad = ole.add_unit(gnome.units.quad_bike, name = 'QuadBikes With Plasma Shield Generator')
ole.add_equipment(quad, gnome.equipments.plasma_shield_generator)


inf = ole.add_unit(gnome.units.gnome_infantry, name = 'Green Gas Infantry')
ole.upgrade_model('Green Gas Infantry', gnome.models.gnome_tinkerer)
ole.upgrade_model('Green Gas Infantry', gnome.models.gnome_tinkerer)
ole.add_equipment(inf, gnome.equipments.green_gas_launcher)
ole.add_equipment(inf, gnome.equipments.green_gas_launcher)
ole.add_equipment(inf, gnome.equipments.plasma_shield_generator)
ole.add_equipment(inf, gnome.equipments.medical_armor)


assault_bot = ole.add_unit(gnome.units.assault_bots)
mechanical_badger = ole.add_unit(gnome.units.mechanical_badger)


ork = data.Race.from_toml("ork")

ga = data.Team("Geir Arnes Ork")

hammerhead = ga.add_unit(ork.units.hammerhead)
bio1=ga.add_unit(ork.units.bioengineered_ork, name = 'Bio1')
bio2=ga.add_unit(ork.units.bioengineered_ork, name = 'Bio2')
superman =ga.add_unit(ork.units.ork_infantry, name = 'Daffy')
inf=ga.add_unit(ork.units.ork_infantry)
ga.upgrade_model("Daffy", ork.models.ork_elite_infantry)
ga.upgrade_model("Daffy", ork.models.ork_elite_infantry)
ga.upgrade_model("Daffy", ork.models.ork_elite_infantry)
ga.upgrade_model("Daffy", ork.models.ork_elite_infantry)
ga.add_unit(ork.units.champion, 'SuperDaffy')

ga.upgrade_model("Bio2", ork.models.elite_bioengineered_ork)
ga.upgrade_model("Bio2", ork.models.elite_bioengineered_ork)
ga.upgrade_model("Bio2", ork.models.elite_bioengineered_ork)
ga.upgrade_model("Bio2", ork.models.elite_bioengineered_ork)

ga.add_equipment("Daffy", ork.equipments.clockwork_wings)
ga.add_equipment("Daffy", ork.equipments.clockwork_shield)

ga.add_equipment("SuperDaffy", ork.equipments.flame_covered_axe_free)
ga.add_equipment("SuperDaffy", ork.equipments.clockwork_wings_free)
ga.add_equipment("SuperDaffy", ork.equipments.clockwork_shield_free)

ga.add_equipment("Daffy", ork.equipments.flame_covered_axe)
ga.add_equipment("Daffy", ork.equipments.flame_covered_axe)
ga.add_equipment("Daffy", ork.equipments.flame_covered_axe)
ga.add_equipment("Daffy", ork.equipments.flame_covered_axe)

ga.add_equipment("Bio1", ork.equipments.ork_pistol)
ga.add_equipment("Bio1", ork.equipments.ork_pistol)
ga.add_equipment("Bio1", ork.equipments.ork_pistol)
ga.add_equipment("Bio1", ork.equipments.ork_pistol)

ga.add_equipment("Bio2", ork.equipments.assault_musket)
ga.add_equipment("Bio2", ork.equipments.assault_musket)

import IPython; IPython.embed()



