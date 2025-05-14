import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 

import data

gnome = data.Race.from_toml("gnome")
dwarf = data.Race.from_toml("dwarf")
ork = data.Race.from_toml("ork")
elf = data.Race.from_toml("elf")
darkelf = data.Race.from_toml("darkelf")




op1 = data.Team("Dwarf SteamPowerArmor with Balrog Assault")

sp = op1.add_unit(dwarf.units.steampowerarmor, name = 'SteamPowerArmor')
op1.add_equipment(sp, dwarf.equipments.vest_of_life_support)
op1.add_equipment(sp, dwarf.equipments.multi_barrled_heavy_musket)

op1.add_unit(dwarf.units.tamed_balrog, name='Tamed Balrog')

op1.add_unit(dwarf.units.zap)
op1.add_unit(dwarf.units.dwarf_infantry, name ='Dwarf Infantry')



oliphant = data.Team("Oliphant attack")

oliphant.add_unit(elf.units.armored_oliphant_riders, name='Oliphant Riders')
#oliphant.add_unit(elf.units.armored_oliphant_riders, name='Oliphant Riders2')
#oliphant.add_unit(elf.units.armored_oliphant_riders, name='Oliphant Riders3')
#oliphant.add_unit(elf.units.armored_oliphant_riders, name='Oliphant Riders4')


oliphant.add_unit(elf.units.e34, name = 'Elf Main Battle Tank')
#oliphant.add_unit(elf.units.e34, name = 'Main Elf Battletank2')



inf = oliphant.add_unit(elf.units.elf_infantry, name='Elf Infantry')
#oliphant.add_equipment(inf, elf.equipments.at_rifle)




import IPython; IPython.embed()

