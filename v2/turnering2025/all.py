import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import data

gnome = data.Race.from_toml("gnome")
dwarf = data.Race.from_toml("dwarf")
ork = data.Race.from_toml("ork")
darkelf = data.Race.from_toml("darkelf")

geirarne = data.Team("Orker ikke")
geirarne.add_unit(ork.units.ork_char_b1)
# geirarne.add_unit(ork.units.ork_char_b1)

bugs = geirarne.add_unit(ork.units.ork_infantry, name="Bugs Bunny")
geirarne.upgrade_model("Bugs Bunny", ork.models.ork_elite_infantry)
geirarne.add_equipment(bugs, ork.equipments.clockwork_power_spear)
geirarne.add_equipment(bugs, ork.equipments.clockwork_wings)

# capn = geirarne.add_unit(ork.units.ork_infantry, name="Kaptein Sabeltann")
# geirarne.upgrade_model("Kaptein Sabeltann", ork.models.ork_elite_infantry)
# geirarne.add_equipment(capn, ork.equipments.clockwork_power_spear)
# geirarne.add_equipment(capn, ork.equipments.clockwork_wings)

bo1 = geirarne.add_unit(ork.units.bioengineered_ork)
geirarne.add_equipment(bo1, ork.equipments.ork_pistol)
geirarne.add_equipment(bo1, ork.equipments.ork_pistol)
geirarne.add_equipment(bo1, ork.equipments.ork_pistol)
geirarne.add_equipment(bo1, ork.equipments.ork_pistol)

# bo2 = geirarne.add_unit(ork.units.bioengineered_ork)
# geirarne.add_equipment(bo2, ork.equipments.ork_pistol)
# geirarne.add_equipment(bo2, ork.equipments.ork_pistol)
# geirarne.add_equipment(bo2, ork.equipments.ork_pistol)
# geirarne.add_equipment(bo2, ork.equipments.ork_pistol)

bbc = geirarne.add_unit(ork.units.champion, "Bugs_Bunny_Champion")
geirarne.add_equipment(bbc, ork.equipments.clockwork_wings)
geirarne.add_equipment(bbc, ork.equipments.clockwork_power_spear)


geirarne.add_unit(ork.units.warg_rider)
# geirarne.add_unit(ork.units.warg_rider)
# geirarne.add_unit(ork.units.warg_rider)
geirarne.add_unit(ork.units.grunt)


knut = data.Team('Assaultbots')

knut.add_unit(gnome.units.ballista_tractor_markI)

mortar = knut.add_unit(gnome.units.gnome_infantry, 'Mortar')
knut.upgrade_model("Mortar", gnome.models.gnome_tinkerer)
knut.add_equipment(mortar, gnome.equipments.assault_bot_mortar)
knut.add_equipment(mortar, gnome.equipments.green_gas_launcher)

deathray = knut.add_unit(gnome.units.gnome_infantry, 'DeathRay Inf with Owl')
knut.upgrade_model(deathray, gnome.models.gnome_tinkerer)
knut.add_equipment(deathray, gnome.equipments.mechanical_owl)
knut.add_equipment(deathray, gnome.equipments.experimental_death_ray)

deathray = knut.add_unit(gnome.units.gnome_infantry, 'DeathRay Inf')
knut.upgrade_model(deathray, gnome.models.gnome_tinkerer)
knut.add_equipment(deathray, gnome.equipments.experimental_death_ray)

knut.add_unit(gnome.units.assault_bots)
knut.add_unit(gnome.units.mechanical_rat)


martin = data.Team('DarkElf')

martin.add_unit(darkelf.units.queen_yy)
martin.add_unit(darkelf.units.mechanical_scorpion)
#martin.add_unit(darkelf.units.mechanical_scorpion)

martin.add_unit(darkelf.units.nightmare_mechanical_cavalry)
#martin.add_unit(darkelf.units.nightmare_mechanical_cavalry)

a1 = martin.add_unit(darkelf.units.roboprosthetic_darkelf, 'SMG Roboprosthetic Infantry')
martin.add_equipment(a1, darkelf.equipments.smg)
martin.add_equipment(a1, darkelf.equipments.integrated_pistol)

#a2 = martin.add_unit(darkelf.units.roboprosthetic_darkelf, 'a2')
#martin.add_equipment(a2, darkelf.equipments.smg)
#martin.add_equipment(a2, darkelf.equipments.integrated_pistol)

i1 = martin.add_unit(darkelf.units.darkelf_infantry, 'SMG Infantry')
martin.add_equipment(i1, darkelf.equipments.smg)
martin.add_equipment(i1, darkelf.equipments.poisonfog_grenade)


#i2 = martin.add_unit(darkelf.units.darkelf_infantry, 'i2')
#martin.add_equipment(i2, darkelf.equipments.smg)
#martin.add_equipment(i2, darkelf.equipments.poisonfog_grenade)


#a3 = martin.add_unit(darkelf.units.roboprosthetic_darkelf, 'a3')
#martin.add_equipment(a3, darkelf.equipments.smg)
#martin.add_equipment(a3, darkelf.equipments.integrated_pistol)

#a2 = martin.add_unit(darkelf.units.roboprosthetic_assasin, 'a2')
#martin.add_equipment(a1, darkelf.equipments.poison_gas_grenade)


morten1 = data.Team('Blast Stick')

morten1.add_unit(dwarf.units.transport_zeppelin)
#morten1.add_unit(dwarf.units.transport_zeppelin)
#morten1.add_unit(dwarf.units.transport_zeppelin)

blast= morten1.add_unit(dwarf.units.dwarf_infantry, 'Blast Stick Infantry')
morten1.upgrade_model(blast, dwarf.models.elite_dwarf_infantry)
morten1.upgrade_model(blast, dwarf.models.elite_dwarf_infantry)
morten1.upgrade_model(blast, dwarf.models.elite_dwarf_infantry)
morten1.upgrade_model(blast, dwarf.models.elite_dwarf_infantry)
morten1.add_equipment(blast, dwarf.equipments.blast_sticks)
morten1.add_equipment(blast, dwarf.equipments.vest_of_life_support)
morten1.add_equipment(blast, dwarf.equipments.trenchcoat_of_resistance)
morten1.add_equipment(blast, dwarf.equipments.industrial_small_arms)

#x6 of these

morten1.add_unit(dwarf.units.gunblasterwagon)
#morten1.add_unit(dwarf.units.gunblasterwagon)
#morten1.add_unit(dwarf.units.gunblasterwagon)


import IPython
IPython.embed()




