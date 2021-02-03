import json
#import pickle
import toml

class Team():
    def __init__(self, name):
        self.name= name
        self.units = {}
        self.weapons = {}
        self.abilities = {}

    def copy_weapons_from(self, other_team):
        for key, unit in self.units.items():
            for weapon_name in unit.weapons_input:
                if weapon_name:
                    self.weapons[weapon_name] = other_team.weapons[weapon_name]
        

    def unit_sort(self, text):
        
        if text.startswith('Elite'):
            used = text[6:] + ' ' + text[0:5]

            try:
                self.units[text[6:]]
                text = text[6:]
            except KeyError:
                used = text
        else:
            used = text

        models = self.units[text].models
                
        try:
            models = str(4-int(models) )
        except:
            print('Number of models not an int')
            
        type_   = self.units[text].type_

        #print(models + type_+used)
        return models + type_+used



    def find_upgrades(self, unit):
        print()
        all = self.weapons.copy()
        all.update(self.abilities)
        upgrades = {}
        
        for key, weapon in all.items():
            if weapon.cost:
                req = weapon.required_to_buy
                req = req.split(':')
                baseORmodel = req[0]
                possible_unit_types = req[1].split(' or ')
                

                type_ = weapon.type_.split(',')[1].strip()

                if baseORmodel == 'Unit Base' and not unit.isReplacement:
                    for p in possible_unit_types:
                        p = p.strip()
                        if p in unit.type_ or p in unit.name:
                            print(key, 'possible addon for ', unit.name)
                            upgrades.setdefault('Unit Base', {})
                            upgrades['Unit Base'].setdefault(type_, [])
                            upgrades['Unit Base'][type_].append(key)

                if baseORmodel == 'Model':
                    for p in possible_unit_types:
                        p = p.strip()
                        p = p.split(' ')
                        test = True
                        for one in p:
                            if not(one in unit.type_ or one in unit.name):
                                test = False
                                    
                        if test:
                            print(key, 'possible addon for ', unit.name)
                            upgrades.setdefault('Model Weapon', {})
                            upgrades['Model Weapon'].setdefault(type_, [])
                            upgrades['Model Weapon'][type_].append(key)

                            if unit.isReplacement:
                                print('  1 possible upgrades per model of this type')
                            else:
                                print('  ', unit.models, ' possible upgrades')

        if not unit.isReplacement:
            for key, other_u in self.units.items():
                if other_u.isReplacement:
                    
                    replaces = other_u.replaces.split(':')
                    replaces = replaces[1].split(' or ')
                    for r in replaces:
                         if r.strip() in unit.name:
                            print(key, 'possible upgrade for ', unit.name)
                            print('  ', unit.models, ' possible upgrades')
                            upgrades.setdefault('Model Replacement', {})
                            upgrades['Model Replacement'].setdefault(key, {})
                            upgrades['Model Replacement'][key] = unit.models
                            
        return upgrades



    def link_all_upgrades(self):
        all_upgrades = {}
        for unit_name in sorted(self.units, key=self.unit_sort):
            unit = self.units[unit_name]
            
            if self.find_upgrades(unit):
                all_upgrades[unit_name] = self.find_upgrades(unit)

        return all_upgrades
        
    def write_pdf(self):

        #Need to be able to read the inputlines
        with open('unit_base_template.tex', 'r') as fid:
            self.unit_base_template = fid.read()
        with open('orders_template.tex', 'r') as fid:        
            self.orders_name_line = fid.readline()
            self.orders_line = fid.readline()

        with open('abilities_template.tex', 'r') as fid:
            self.abilities_template = fid.read()
        
                 
            
        with open('damage_template.tex', 'r') as fid:        
            self.damage_name_line = fid.readline()
            self.damage_line = fid.readline()

        #weapon which are prepaid for by the unit
        with open('weapon_template.tex', 'r') as fid:
            self.weapon_template = fid.read()

        with open('assault_template.tex', 'r') as fid:
            self.assault_template = fid.read()

        with open('combined_template.tex', 'r') as fid:
            self.combined_template = fid.read()

        with open('ranged_template.tex', 'r') as fid:
            self.ranged_template = fid.read()

        with open('misc_template.tex', 'r') as fid:
            self.misc_template = fid.read()

        with open('model_replacement_template.tex', 'r') as fid:
            self.model_replacement_template = fid.read()
            
        latex_unit = ""
        latex_equipment_upgrade = ""
    
        for unit_name in sorted(self.units, key=self.unit_sort):
            print('working on ', unit_name)
            unit = self.units[unit_name]
            if unit.retired == 'yes':
                continue
            
            latex_order = ""
            latex_damage = ""
            latex_weapons = ""
            for order_name in unit.__dict__['orders'].keys():
                d1 = {'order_name' : order_name}
                latex_order = latex_order + self.orders_name_line.format(**d1)
                for line in unit.__dict__['orders'][order_name]:
                    d2 = {'orders_line': line}
                    latex_order = latex_order + self.orders_line.format(**d2)

            for damage_name in unit.__dict__['damage_tables'].keys():
                d1 = {'damage_name' : damage_name}
                latex_damage = latex_damage + self.damage_name_line.format(**d1)
                for line in unit.__dict__['damage_tables'][damage_name]:
                    d2 = {'damage_line': line}
                    latex_damage = latex_damage + self.damage_line.format(**d2)

                
            for weapon_name in unit.weapons_input:
                if weapon_name:
                    weapon = self.weapons[weapon_name]
                    latex_weapons = latex_weapons + self.weapon_template.format(**weapon.__dict__)
                  
            combined_dict = unit.__dict__.copy()
            combined_dict['orders'] = latex_order
            combined_dict['damage'] = latex_damage
            combined_dict['weapon'] = latex_weapons

            if unit.isReplacement == 'yes':
                latex_unit = latex_unit + self.model_replacement_template.format(**combined_dict)
            else:
                latex_unit = latex_unit + self.unit_base_template.format(**combined_dict)
            #print(latex_unit)

        for weapon_name in sorted(self.weapons.keys()):

            if weapon_name:
                weapon = self.weapons[weapon_name]
                if weapon.cost:
                    if weapon.template == 'a':
                        template = self.assault_template
                    if weapon.template == 'r':
                        template = self.ranged_template
                    if weapon.template == 'ra':
                        template = self.combined_template
                    if weapon.template == 'misc':
                        template = self.misc_template
                    if weapon.template == '':
                        template = ''
                        print('Missing weapon template', weapon_name)
                    else:
                        print('working on ', weapon_name)
                        
                    orders_gained = ''
                    orders_lost   = ''
                    for o in weapon.orders_gained:
                        if o:
                            orders_gained = orders_gained + o + r'\\'

                    for o in weapon.orders_lost:
                        if o:
                            orders_lost = orders_lost + o + r'\\'

                    combined = weapon.__dict__.copy()
                    combined['orders_gained'] = orders_gained
                    combined['orders_lost'] = orders_lost
    
                    latex_equipment_upgrade = latex_equipment_upgrade + template.format(**weapon.__dict__)

        latex_abilities = ''
        for ability_name in self.abilities.keys():
            ability = self.abilities[ability_name]

            orders_gained = ''
            orders_lost   = ''
            
            for o in ability.orders_gained:
                if o:
                    orders_gained = orders_gained + o + r'\\'

            for o in ability.orders_lost:
                if o:
                    orders_lost = orders_lost + o + r'\\'

            combined = ability.__dict__.copy()
            combined['orders_gained'] = orders_gained
            combined['orders_lost'] = orders_lost

            latex_abilities = latex_abilities + self.abilities_template.format(**combined)
            
        latex = latex_abilities + latex_unit + '\pagebreak' + latex_equipment_upgrade
                                
        with open(self.name +'.tex', 'w') as fid:
                fid.write(latex)

                                        
                        
                
                
    def add_team_order(self, name, l):
        
        if name in self.orders.keys():
                self.orders[name].append(l)
        else:
                print('first time orders for ', name, ' is give')
                self.orders[name] = [l]
                
        
    def store_data(self):
        self.write_json()
        self.write_toml()
        
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
        
        print(d)
        return d

    def write_toml(self):
        d = self.write_dict()

        with open(self.name + '.toml', 'w') as outfile:
                toml.dump(d, outfile)


    def from_toml(self):
        nested_keys = ['units', 'weapons']
            
        d0 = self.write_dict()
        with open(self.name + '.toml', 'r') as f:
                d1 = toml.load(f)

                #print(d1)

        print(d0.keys())
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

                      
    def write_json(self):
        d = self.write_dict()
     
        with open(self.name+ '.json', 'w') as outfile:  
            json.dump(d, outfile)
        
            
    def append_unit(self, unit):
        self.units[unit.name] = unit
        
    def append_weapon(self, weapon):
        self.weapons[weapon.name] = weapon


    def append_ability(self, ability):
        self.abilities[ability.name] = ability



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
        
    def write(self):
        for key in sorted(self.__dict__.keys() ):
            text = self.__dict__[key]
            if self.__dict__[key] == '':
                self.__dict__[key] = input(key + ': ')

            if self.__dict__[key] == []:
                more = True
                while more:
                    self.__dict__[key].append(input('Add ' + key+':') )
                    another = input('add another input? y/n:')
                    if another == 'y':
                        more= True
                    else:
                        more = False
            
            else:
                print(key, ': ', self.__dict__[key])

        self.team.append_weapon(self)
    
    def add_to(self, key):
        try:
                self.__dict__[key]
        except KeyError:
                print('KeyError')
                retrun

        addision = input('Add extra line to ' + key + ':')
        self.__dict__[key] = self.__dict__[key] + addision        

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

        
    def update(self):
        self.team.append_weapon(self)
        
    def write(self):
        for key in sorted(self.__dict__.keys() ):
            text = self.__dict__[key]
            if self.__dict__[key] == '':
                self.__dict__[key] = input(key + ': ')

            if self.__dict__[key] == []:
                more = True
                while more:
                    self.__dict__[key].append(input('Add ' + key+':') )
                    another = input('add another input? y/n:')
                    if another == 'y':
                        more= True
                    else:
                        more = False
            
            else:
                print(key, ': ', self.__dict__[key])

        self.team.append_weapon(self)
    
    def add_to(self, key):
        try:
                self.__dict__[key]
        except KeyError:
                print('KeyError')
                retrun

        addision = input('Add extra line to ' + key + ':')
        self.__dict__[key] = self.__dict__[key] + addision        

        
class Unit():

    def __init__(self, name , team):
        self.team = team
        self.race = team.name
        self.name = name
        self.models = ''
        self.size = ''
        self.cost = ''
        self.armor = ''
        self.type_ = ''
        self.isReplacement = ''
        self.replaces = ''
        self.unititems = ''
        self.modelitems = ''
        self.retired = ''
        
        self.weapons_input= []
        
        self.unit_special = ''


        self.assault = ''
        self.assault_die = ''
        self.assault_deflection_die = ''
        self.assault_damage = ''
        self.assault_ap = ''
        self.assault_deflection = ''
        self.assault_special = ''
 
        
        self.orders = {}

        self.damage_tables = {}

        self.filters = ['weapons', 'team']


    def add_to(self, key):
        try:
                self.__dict__[key]
        except KeyError:
                print('KeyError')
                retrun

        addision = input('Add extra line to ' + key + ':')
        self.__dict__[key] = self.__dict__[key] + addision
                
        #import IPython; IPython.embed()

    def from_dict(self, d0):
        d1 = self.write_dict()
        for key in d1:
                try:
                    setattr(self, key, d0[key])
                except KeyError:
                    if key == 'orders':
                        setattr(self, key, {})
                    else:
                        setattr(self, key, '')
        
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


        
    def write(self):
        for key in sorted(self.__dict__.keys() ):
            text = self.__dict__[key]
            if self.__dict__[key] == '':
                self.__dict__[key] = input(key + ': ')

            if self.__dict__[key] == []:
                more = True
                while more:
                    self.__dict__[key].append(input('Add ' + key+':') )
                    another = input('add another input? y/n:')
                    if another == 'y':
                        more= True
                    else:
                        more = False

            if self.__dict__[key] == {}:
                more = True
                while more:
                        name = input(key + ' name:')
                        self.__dict__[key][name] =[]
                        more2 = True
                        while more2:
                                self.__dict__[key][name].append(input('add an input for ' +name + ':') )
                                another = input('Add one more element? y/n:')

                                if another == 'y':
                                        more2= True
                                else:
                                        more2 = False

                        another = input('Add one more ' + key + ' name? y/n:')
                        if another == 'y':
                                more2= True
                        else:
                                more = False

            
            else:
                print(key, ': ', self.__dict__[key])

        self.team.append_unit(self)            



class Costimized_unit(Unit):
    def __init__(self, name, team):
        super().__init__(name, team)
        self.replacements = {}
        self.replacements_types = {}

    def write():
        pass
        
    def base_unit(self, unit):
        self.baseunitname = unit.name
        self.models = unit.models
        self.size = unit.size
        self.cost = unit.cost
        self.armor = unit.armor
        self.type_ = unit.type_
        self.unititems = unit.unititems
        self.modelitems = unit.modelitems
        
        self.orders = unit.orders

        self.damage_tables = unit.damage_tables

        self.filters = ['weapons', 'team']
        
        self.unit_special = unit.unit_special


        
        self.assault = unit.assault
        self.assault_die = unit.assault_die 
        self.assault_deflection_die = unit.assault_deflection_die 
        self.assault_damage = unit.assault_damage 
        self.assault_ap = unit.assault_ap 
        self.assault_deflection = unit.assault_deflection
        self.assault_special = unit.assault_special 
 
        self.weapons_input= unit.weapons_input




        
    def add_replacement(self, replacement):

       self.models = int(self.models)-1
       try:
           costimized_unit.replacements[replacement.name] = costimized_unit.replacements[replacement.name] +1 
       except KeyError:
           costimized_unit.replacements[replacement.name] = 1
           costimized_unit.replacement_types[replacement.name] = replacement 




        
if __name__ == "__main__":        
    import IPython; IPython.embed()
