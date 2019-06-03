import json
import pickle
import toml

def read_pickle(name):
        with open(name+'.pcl','rb') as fid:
                return pickle.load(fid)

class Team():
    def __init__(self, name):
        self.name= name
        self.units = {}
        self.weapons = {}
        self.orders = {}
        
    def add_team_order(self, name, l):
        
        if name in self.orders.keys():
                self.orders[name].append(l)
        else:
                print('first time orders for ', name, ' is give')
                self.orders[name] = [l]
                
        
    def store_data(self):
        self.write_json()
        self.write_pickle()
        self.write_toml()
        
    def write_dict(self):
        d = {}
        d['name'] = self.name
        d['orders'] = self.orders
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
                self.weapons[weapon_name] = Unit(weapon_name, self)
                rest_dict= d1['weapons'][weapon_name]
                self.weapons[weapon_name].team = self
                self.weapons[weapon_name].from_dict(rest_dict)


                      
    def write_json(self):
        d = self.write_dict()
     
        with open(self.name+ '.json', 'w') as outfile:  
            json.dump(d, outfile)
        
            
    def write_pickle(self):
        """save class as self.name.pcl"""
        with open(self.name+'.pcl','wb') as fid:
            pickle.dump(self, fid)

    
                
            
    def append_unit(self, unit):
        self.units[unit.name] = unit
        
    def append_weapon(self, weapon):
        self.weapons[weapon.name] = weapon



class Weapon():
    def __init__(self, name, team):

        self.team = team
        self.race = team.name
        self.name = name
        self.range_ = ''
        self.angle = ''
        self.special = ''
        self.damage = ''
        self.pen    = ''
        self.ap = ''
        self.assault_mod = ''
        self.assault_deflection_mod = ''
        self.assault_deflection_die_set_to = ''
        self.assault_dam_set_to = ''
        self.assault_pen_set_to = ''
        self.assault_special = ''
        self.assault_ap = ''
        self.orders_gained = []
        self.orders_lost = []
        self.cost = ''
        self.requiered_to_buy = ''
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
        self.members = ''
        self.size = ''
        self.cost = ''
        self.armor = ''
        self.type_ = ''


        self.weapons_input= []
        
        self.unit_special = ''

        self.assault = ''
        self.assault_die = ''
        self.assault_deflection_die = ''
        self.assualt_damage = ''
        self.assualt_pen = ''
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
                
                
        
import IPython; IPython.embed()
