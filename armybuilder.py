import toml

from copy import deepcopy


class Team():
    def __init__(self, name):
        self.name= name
        self.units = {}
        self.models = {}
        self.weapons = {}
        self.abilities = {}
        self.models = {}
        self.personal_team = {}

    def upgrades(self, unit):

        upgrades = {}

        possible_models = {}
        
        for model_name, model in self.models.items():
            if model.isReplacement == 'yes':
                for n in range(len(unit.model_list)):
                    modelINunit = unit.model_list[n]
                    tmp = model.replaces.split(':')
                    tmp2 = tmp[1].split('or')
                    model_replacements = [m.strip().lower() for m in tmp2]
                    if modelINunit.name.strip().lower() in model_replacements:
                        upgrades[model.name] = model
                        possible_models.setdefault(model_name, [])
                        possible_models[model_name].append(n)
                        
        for weapon_name,weapon in self.weapons.items():

            
            if weapon.cost == '':
                continue

            
            
            allreadyequiped = [a for a in unit.unit_base_weapons.keys()]
            
            if weapon.name in allreadyequiped:
                continue

            allreadyequiped = [a for a in unit.misc_equipment.keys()]

            if weapon.name in allreadyequiped:
                continue
            
            tmp = weapon.required_to_buy.split(':')

            modelORunit = tmp[0]
            required = tmp[1].split(' or ')


            types = [a.strip().lower() for a in unit.type_.split(',')]
            types.append(unit.name.strip().lower())


            #print(weapon.name)
            ##check if unit meets the requirements of the item.
            #print(modelORunit)
            if modelORunit.strip().lower() == 'unit base':
             
                for r in required:
                    still_true = True
                    if r.strip().lower() not in types:
                        still_true = False

                    if still_true:
                        break 
                        
                if not still_true:
                    continue
                
                          
            if modelORunit.strip().lower() == 'model':
                #import IPython; IPython.embed()
                eligable_models = []
                
                for n in range(len(unit.model_list)):
                    m = unit.model_list[n]
                    #print(m.name)
                    for r in required:
                        types = [a.strip().lower() for a in m.type_.split(',')]
                        types.append(m.name.strip().lower())

                        still_true = True
                        if r.strip().lower() not in types:
                            still_true = False
                            continue

                        eligable_models.append(n)

            else:
                eligable_models = range(len(unit.model_list))


            if not eligable_models:
                continue

            handed = ['1handed weapon', '2handed weapon', '3handed weapon', '4handed weapon']
            hands = ['1 hands', '2 hands', '3 hands', '4 hands']

            ##check if the weapon meets the requirements of the unit.
            unit_items = unit.unititems.split(',')
            type_ = weapon.type_.split(',')[1]
            type_ = type_.lower().strip()


            modified_unit_items = []
            for u in unit_items:
                tmp = u.strip()
                tmp = tmp[1:]
                tmp = tmp.strip().lower()

                modified_unit_items.append(tmp)


            #print(type_.strip().lower(), modified_unit_items)

            #print('in modified_unit_items?')

            if not type_ in modified_unit_items:
                still_true = False

            #print('1', weapon.name)
            if not still_true:
                
                if int(unit.models) > 0:

                    for n in eligable_models:
                        
                        model = unit.model_list[n]
                        
                        still_true = True

                        
                        model_items = model.modelitems.split(',')
                        model_items = [a.lower().strip() for a in model_items]
                        mod = []

                        
                        for m in model_items:
                          
                            if not m:
                                continue

                            if m.strip()[-5:] == 'hands':
                                mod.append(m)
                                continue


                      
                            if m[0].isdigit():
                                if m[1].isdigit():
                                    mod.append(m[2:].strip())
                                else:
                                    mod.append(m[1:].strip())
                                    
                            if m.startswith('unlimited'):
                                mod.append(m[9:].strip())

                        model_items = mod
                        
                        if not type_ in model_items:
                            if type_ in handed:
                            
                                numberofhands_required = int(type_[0])
                                numberof_modelhands  = 0
                            
                                
                                for m in model_items:
                                    if m in hands:
                                        
                                        numberof_modelhands = int(m[0])

                                if numberofhands_required > numberof_modelhands:
                                    still_true = False

                        if modelORunit == 'unit' and (not still_true):
                            break

                        if still_true:
                            possible_models.setdefault(weapon.name, [])
                            possible_models[weapon.name].append(n)

                if still_true:
                    upgrades[weapon_name] = weapon

        return upgrades, possible_models
    
    def write_dict(self):
        d = {}
        d['name'] = self.name
        
        for key in self.weapons.keys():
                weapon = self.weapons[key]
                d.setdefault('weapons', {})
                if type(weapon) == Weapon:         
                    d['weapons'][weapon.name] = weapon.write_dict()
                    
        for key in self.units.keys():
                unit = self.units[key]
                d.setdefault('units', {})
                if type(unit) == Unit:
                    d['units'][unit.name] = unit.write_dict()

        for key in self.abilities.keys():
                ability = self.abilities[key]
                d.setdefault('abilities', {})
                if type(ability) == Ability:
                        d['abilities'][ability.name] = ability.write_dict()
        
        #print(d)
        return d
        
    def from_toml(self):
        nested_keys = ['units', 'weapons']
            
        d0 = self.write_dict()
        with open(self.name + '.toml', 'r') as f:
                d1 = toml.load(f)

                #print(d1)

        #import IPython; IPython.embed()
                
        #print(d0.keys())
        for key in d0.keys():
                if key not in nested_keys:
                        try:
                                setattr(self, key, d1[key])
                        except KeyError:
                                setattr(self, key, '')
               
        for unit_name in d1['units'].keys():
            self.units[unit_name] = Unit(unit_name, self)
            rest_dict= d1['units'][unit_name]
            self.units[unit_name].team = self
            self.units[unit_name].from_dict(rest_dict)
            if d1['units'][unit_name]['isReplacement'] == 'yes':
                self.units.pop(unit_name)
            if d1['units'][unit_name]['retired'] == 'yes':
                self.units.pop(unit_name)
            
                
        for weapon_name in d1['weapons'].keys():
            self.weapons[weapon_name] = Weapon(weapon_name, self)
            rest_dict= d1['weapons'][weapon_name]
            self.weapons[weapon_name].team = self
            self.weapons[weapon_name].from_dict(rest_dict)

        try:                
            for ability_name in d1['abilities'].keys():
                self.abilities[ability_name] = Ability(ability_name, self)
                rest_dict= d1['abilities'][ability_name]
                self.abilities[ability_name].team = self
                self.abilities[ability_name].from_dict(rest_dict)
        except KeyError:
            print('No abilities')

        

class Weapon():
    def __init__(self, name, team):

        self.team = team
        self.race = team.name
        self.name = name
        self.template = ''         
        self.range_ = ''
        self.angle = ''
        self.special = ''
        self.damage = ''
        self.ap = ''
        self.assault_mod = ''
        self.assault_deflection_mod = ''
        self.assault_deflection_die_set_to = ''
        self.assault_dam_set_to = ''
        #self.assault_pen_set_to = ''
        self.assault_special = ''
        self.assault_ap = ''
        self.orders_gained = []
        self.orders_lost = []
        self.cost = ''
        self.required_to_buy = ''
        #type = unit base, 1 handed, 2 handed, misc, etc...
        self.type_ = ''
        self.filters = ['team']
        
    def write_dict(self):
        d = self.__dict__.copy()

        for f in self.filters:
                try:
                        d.pop(f)
                except KeyError:
                        continue

        #add filters if neccessary
        
        
        return d

    def from_dict(self, d0):
        d1 = self.write_dict()
        for key in d1:
                try:
                        setattr(self, key, d0[key])
                except KeyError:
                        setattr(self, key, '')

        
 
class Unit():

    def __init__(self, name , team):
        self.team = team
        self.race = team.name
        self.name = name
        self.models = ''
        self.default_model_name = self.name
        self.size = ''
        self.cost = ''
        self.armor = ''
        self.type_ = ''
        self.unit_special = ''

        self.unititems = ''
        self.retired = ''

        self.unit_base_weapons= {}
        self.misc_equipment = {}
        
        self.model_list = []
        
        self.orders = {}

        self.damage_tables = {}

        self.filters = ['weapons', 'team']


    def add_upgrade(self, upgrade, possible_models):
        tmp_list = []
        for model in self.model_list:
            model = deepcopy(model)
            tmp_list.append(model)
            self.model_list = tmp_list
            

        if type(upgrade) is Model:
            model = deepcopy(upgrade)

            self.model_list[possible_models[0]] = model
      
            return

        
        type_ = upgrade.type_.split(',')[1]

        tmp = upgrade.required_to_buy.split(':')

        #print(weapon.name)
            
        modelORunit = tmp[0]
        required = tmp[1].split(' or ')

        
        if type_.lower().strip() == "unit base weapon":
            self.unit_base_weapons[upgrade.name] = upgrade

        if type_.lower().strip().endswith("independent equipment"):
            self.misc_equipment[upgrade.name] = upgrade
            
        else:
            if modelORunit.strip().lower() == 'unit base':
                for n in possible_models:
                    model = self.model_list[n]
                    model.add_equipment(upgrade)
                    model.weapons_input = list(filter(None, model.weapons_input))

            else:
                model = self.model_list[possible_models[0]]
                model.add_equipment(upgrade)
                model.weapons_input = list(filter(None, model.weapons_input))

                    

            
    def from_dict(self, d0):
        d1 = self.write_dict()
        for key in d1:
                try:
                    setattr(self, key, d0[key])
                except KeyError:
                    if key == 'orders':
                        setattr(self, key, {})
                    elif key == 'model_list':
                        setattr(self, key, [])
                    elif key == 'unit_base_weapons':
                        setattr(self, key, {})

                    elif key == 'misc_equipment':
                        setattr(self, key, {})
                    else:
                        setattr(self, key, '')

        #print(self.model_list)
        #print(self.models)
        try:
            n = int(self.models)
        except ValueError:
            n = 0

        #print(n)
        
        if self.name not in self.team.models.keys():
            m = Model(self.team, self.name, self)
            m.from_dict(d0)
            self.team.models[self.name] = m
            
        for i in range(n):
            m = Model(self.team, self.name, self)
            m.from_dict(d0)
            #c = deepcopy(m)
            
            self.model_list.append(m)
            

            
        
        
                        
    def write_dict(self):

        d = self.__dict__.copy()
        
        for f in self.filters:
                try:
                        d.pop(f)
                except KeyError:
                        continue
       
        return d
        
    def autofind_weapon_stats(self):
        self.weapons = {}

        for weapon in self.unit_base_weapons_input:
            if type(weapon) != Weapon:
                if weapon == '':
                    print('write name of weapon. It must exists in team.weapon_names')
                else:
                    try:
                        tmp_weapon = self.team.__dict__['weapons'][weapon]
                        self.weapons[weapon] = tmp_weapon
                    except:
                        print('unkown weapon, update teams weapon or check spelling')
            
                    #adjust_orders. First remove lost orders:
                    self.orders = [i for i in self.orders if i not in tmp_weapon.orders_lost]

                    #then add new orders
                    for gained in tmp_weapon.orders_gained:
                            self.orders.append(gained)

    
            
    def auto(self):
        self.autofind_weapon_stats()


        


class Model():
    def __init__(self, team, name, unit):
        self.team = team
        self.race = team.name
        self.name = name

        self.isReplacement = ''
        self.replaces = ''
        self.unit_name = unit.name
        self.type_ = ''
        self.weapons_input= []
        self.extra_equipment = []
        
        self.special = ''
        self.modelitems = ''


        self.assault = ''
        self.assault_die = ''
        self.assault_deflection_die = ''
        self.assault_damage = ''
        self.assault_ap = ''
        self.assault_deflection = ''
        self.assault_special = ''
        self.filters = ['weapons', 'team', 'models']

    def write_dict(self):

        d = self.__dict__.copy()
        
        for f in self.filters:
                try:
                        d.pop(f)
                except KeyError:
                        continue
       
        return d

    def add_equipment(self, equipment):
        type_ = equipment.type_.split(',')[1]
        firstword = type_.strip().split(' ')[0]

        #print(firstword[0][1:5])

        newmodelitems = []
        if firstword[1:5] == 'hand':
            self.weapons_input.append(equipment)
            numberofhandsrequired = int(firstword[0])
            for modelitem in self.modelitems.split(','):
                if 'hands' in modelitem:
                    handstouse = int(modelitem.strip()[0]) - numberofhandsrequired
                    if handstouse < 1:
                        continue
                    else:
                        modifiedmodelitem = str(handstouse) + ' hands'
                else:
                    modifiedmodelitem = modelitem

                newmodelitems.append(modifiedmodelitem)

                
                    

            self.modelitems = ','.join(newmodelitems).strip()
        else:
            self.extra_equipment.append(equipment)
        

        
    
    def from_dict(self, d0):
        d1 = self.write_dict()
        for key in d1:
                try:
                    setattr(self, key, d0[key])
                except KeyError:
                    if key == 'orders':
                        setattr(self, key, {})
                    elif key == 'extra_equipment':
                        setattr(self, key, [])
                    elif key == 'weapons':
                        setattr(self, key, [])
                    else:
                        setattr(self, key, '')
        
    def autofind_weapon_stats(self):
        self.weapons = {}

        for weapon in self.weapons_input:
            if type(weapon) != Weapon:
                if weapon == '':
                    print('write name of weapon. It must exists in team.weapon_names')
                else:
                    try:
                        tmp_weapon = self.team.__dict__['weapons'][weapon]
                        self.weapons[weapon] = tmp_weapon
                    except:
                        print('unkown weapon, update teams weapon or check spelling')
            
                    #adjust_orders. First remove lost orders:
                    self.orders = [i for i in self.orders if i not in tmp_weapon.orders_lost]

                    #then add new orders
                    for gained in tmp_weapon.orders_gained:
                            self.orders.append(gained)

    
            
    def auto(self):
        self.autofind_weapon_stats()


class Ability():
    def __init__(self, name, team):

        self.team = team
        self.race = team.name
        self.name = name
        self.type_ = ''
        
        self.special = ''

        self.orders_gained = []
        self.orders_lost = []
        self.cost = ''

        self.required_to_buy = ''

        self.operational_by = ''
        
        self.filters = ['team']
        
    def write_dict(self):
        d = self.__dict__.copy()

        for f in self.filters:
                try:
                        d.pop(f)
                except KeyError:
                        continue

        #add filters if neccessary
        
        return d

    def from_dict(self, d0):
        d1 = self.write_dict()
        for key in d1:
                try:
                        setattr(self, key, d0[key])
                except KeyError:
                        setattr(self, key, '')

        
    def update(self):
        self.team.append_ability(self)

        

import IPython; IPython.embed()

