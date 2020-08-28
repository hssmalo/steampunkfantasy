from data import Team

elf = Team('Elf')
elf.from_toml()


knut = Team('StandarElf')

knut.units['Tattoo Ink'] = elf.units['Tattoo Ink']
knut.units['Bear Rider'] = elf.units['Bear Rider']
knut.units['Infantry'] = elf.units['Infantry']
knut.units['Illusion'] = elf.units['Illusion']

knut.weapons['Camuflouflage'] = elf.weapons['Camuflouflage']
knut.weapons['Enhanced Rifle'] = elf.weapons['Enhanced Rifle']
knut.weapons['Small grenade'] = elf.weapons['Small grenade']

knut.copy_weapons_from(elf)

knut.write_pdf()

de = Team('DarkElf')
de.from_toml()

bjorn = Team('StandarDarkElf')

bjorn.units['Mechanical Assault Spider'] = de.units['Mechanical Assault Spider']
bjorn.units['Elite Mechanical Cavalry'] =de.units['Elite Mechanical Cavalry']
bjorn.units['Infantry'] = de.units['Infantry']

bjorn.weapons['Mechanical Imp'] = de.weapons['Mechanical Imp']

bjorn.copy_weapons_from(de)

bjorn.write_pdf()

dwarf = Team('Dwarf')
dwarf.from_toml()

ole = Team('StandarDwarf')

ole.units['Dwarf Infantry'] =  dwarf.units['Dwarf Infantry']
ole.units['Tamed Balrog'] = dwarf.units['Tamed Balrog']
ole.units['GunBlasterWagon'] = dwarf.units['GunBlasterWagon']

ole.weapons['Wheeled Shield Wall'] = dwarf.weapons['Wheeled Shield Wall']
ole.weapons['Heavy Musket'] = dwarf.weapons['Heavy Musket']

ole.copy_weapons_from(dwarf)

ole.write_pdf()

ga = Team('StandarOrk')

ork = Team('Ork')
ork.from_toml()

ga.units['BioEngineered Ork'] = ork.units['BioEngineered Ork']
ga.units['Grunt'] = ork.units['Grunt']
ga.units['Warg Rider'] = ork.units['Warg Rider']
ga.units['Speedhead'] = ork.units['Speedhead']

ga.weapons['Ork Pistol'] = ork.weapons['Ork Pistol']
ga.weapons['Clockwork Monocular'] = ork.weapons['Clockwork Monocular']
ga.weapons['Clockwork Shield'] = ork.weapons['Clockwork Shield']
ga.weapons['Flame-covered-axe'] = ork.weapons['Flame-covered-axe']

ga.copy_weapons_from(ork)

ga.write_pdf()
