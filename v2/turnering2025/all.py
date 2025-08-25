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

geirarne.add_unit(ork.units.warg_rider)
# geirarne.add_unit(ork.units.warg_rider)
# geirarne.add_unit(ork.units.warg_rider)
geirarne.add_unit(ork.units.grunt)

import IPython

IPython.embed()
