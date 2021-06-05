import collections
import functools
import itertools
import pathlib
import re
from dataclasses import dataclass, field

import munch
from pyconfs import Configuration


class CounterList(collections.UserList):
    @property
    def names(self):
        return {item.name for item in self.data}

    def as_dict(self):
        items = {}
        for item in self.data:
            items.setdefault(item.name, []).append(item)

        return items

    def __str__(self):
        return ", ".join(f"{len(v)} x {n}" for n, v in self.as_dict().items())

    def __repr__(self):
        return f"'{self}'"


@dataclass
class Costs:
    ip: int = 0  # Industry points
    mp: int = 0  # Manpower
    cp: int = 0  # Crafts points
    xp: int = 0  # Xperience points
    command: int = 0  # Command

    @classmethod
    def from_string(cls, string):
        """Parse a string of costs"""
        cost_strings = string.split()
        costs = {
            "".join(c for c in s if c.isalpha()): int(
                "".join(c for c in s if c.isdigit())
            )
            for s in cost_strings
            if re.match(r"(\d+)([a-z]+)", s)
        }
        return cls(**costs)

    @classmethod
    def from_toml(cls, cfg):
        """Convert a config or a dictionary to a Costs object"""
        return cls(**{k: v for k, v in cfg.items() if k in cls.__dataclass_fields__})

    @property
    def victory_points(self):
        """Victory points are calculated from costs"""
        return 3 * self.ip + self.mp + self.cp + self.xp + self.command

    def __bool__(self):
        """A Costs object is False when all costs are 0"""
        return any(self.__dict__.values())

    def __add__(self, other):
        """Add two Costs together"""
        return self.__class__(
            **{k: s + getattr(other, k) for k, s in self.__dict__.items()}
        )

    def __sub__(self, other):
        """Subtract one Costs from another"""
        return self.__class__(
            **{k: s - getattr(other, k) for k, s in self.__dict__.items()}
        )

    def __mul__(self, other):
        """Multiply a Costs by a number"""
        return self.__class__(**{k: s * other for k, s in self.__dict__.items()})

    def __rmul__(self, other):
        """Multiply a Costs by a number"""
        return self.__class__(**{k: s * other for k, s in self.__dict__.items()})

    def __ge__(self, other):
        """A Costs is >= than another, if all costs are >="""
        return all(v >= other.__dict__[k] for k, v in self.__dict__.items())

    def __gt__(self, other):
        """A Costs is > than another, if all costs are >"""
        return all(v > other.__dict__[k] for k, v in self.__dict__.items())

    def __str__(self):
        """Represent a cost as a list of positive costs"""
        return ", ".join(f"{v}{k}" for k, v in self.__dict__.items() if v != 0)


@dataclass
class Race:
    label: str
    units: munch.Munch = field(default_factory=munch.Munch)
    models: munch.Munch = field(default_factory=munch.Munch)
    equipments: munch.Munch = field(default_factory=munch.Munch)
    info: Configuration = field(default_factory=Configuration, repr=False)

    def write_info(self, long_=True, format_='tex'):
        txt = ''

        for name, unit in self.units.items():

                
            txt = txt + unit.write_info(long_=long_, format_=format_)

            if format_ == 'tex':
                txt = txt + '\\pagebreak'

        if format_ == 'tex':
            txt = txt + '\\section{Upgradeable Units}'
                
        for name, model in self.models.items():

            try:
                model.info.cost
            except AttributeError:
                continue

            txt = txt + model.write_info(long_, format_)

        if format_ == 'tex':
            txt = txt + '\\section{Equipment and training Upgrades}'
            
        for name, eq in self.equipments.items():

            try:
                eq.info.cost
            except AttributeError:
                continue

            txt = txt + eq.write_info(long_, format_)
            
        if format_ =='tex':
            filename = self.label +'.tex'

            with open(filename, 'w') as fid:
                fid.write(txt)
  
    
    @classmethod
    def from_toml(cls, race):
        toml = _all_tomls()
        if race not in toml.races.section_names:
            races = ", ".join(toml.races.section_names)
            raise ValueError(f"Unknown race {race!r}. Use one of {races}")

        units = munch.Munch(
            **{
                k: Unit.from_toml(k)
                for k, u in toml.units.section_items
                if u.race == race
            }
        )
        models = munch.Munch(
            **{
                k: Model.from_toml(k)
                for k, m in toml.models.section_items
                if m.race == race
            }
        )
        equipments = munch.Munch(
            **{
                k: Equipment.from_toml(k)
                for k, e in toml.equipments.section_items
                if e.race == race
            }
        )

        return cls(
            race,
            units=units,
            models=models,
            equipments=equipments,
            info=toml.races[race],
        )

    @property
    def name(self):
        return self.info["name"]

    def __str__(self):
        return self.name


@dataclass
class Team:
    name: str
    funds: Costs = Costs(ip=24, mp=24, cp=24, xp=24, command=0)
    units: munch.Munch = field(default_factory=munch.Munch)

    def available_units(self, race):
        """List units that are available with the current funds"""
        return {k: v for k, v in race.units.items() if self.funds >= v.cost}

    def add_unit(self, unit, name=None):
        if name in self.units:
            raise ValueError(
                f"Team {self.name!r} already contains a unit named {name!r}"
            )

        if not self.funds >= unit.cost:
            raise ValueError(
                f"Unit {unit.name!r} costs {unit.cost} "
                f"which is more than available funds ({self.funds})"
            )

        if name is None:
            for id in itertools.count(start=1):
                name = f"{unit.name} {id}"
                if name not in self.units:
                    break

        self.units[name] = unit
        self.funds = self.funds - unit.cost

        return name

    def _assert_unit_exists(self, unit_name):
        """Raise error if unit_name is unknown"""
        if unit_name not in self.units:
            units = ", ".join(self.units.keys())
            raise ValueError(f"Unknown unit {unit_name!r}. Use one of {units}")

    def available_upgrades(self, unit_name, race):
        """List available upgrades for a given unit with the current funds"""
        self._assert_unit_exists(unit_name)
        return {
            k: m
            for k, m in self.units[unit_name].available_upgrades(race).items()
            if self.funds >= self.units[unit_name].calculate_model_cost(m)
        }

    def upgrade_model(self, unit_name, model):
        """Replace model in unit"""
        self._assert_unit_exists(unit_name)
        unit = self.units[unit_name]

        cost = unit.calculate_model_cost(model)
        if not self.funds >= cost:
            raise ValueError(
                f"Upgrading to {model.name!r} costs {cost} "
                f"which is more than available funds ({self.funds})"
            )

        self.units[unit_name] = unit.upgrade_model(model)
        self.funds = self.funds - cost

    def available_equipment(self, unit_name, race):
        """List available equipment for the given unit"""
        self._assert_unit_exists(unit_name)

        return {
            k: e
            for k, e in self.units[unit_name].available_equipment(race).items()
            if self.funds >= self.units[unit_name].calculate_equipment_cost(e)
        }

    def add_equipment(self, unit_name, equipment):
        """Add equipment to a unit"""
        self._assert_unit_exists(unit_name)
        unit = self.units[unit_name]

        cost = unit.calculate_equipment_cost(equipment)
        if not self.funds >= cost:
            raise ValueError(
                f"Adding {equipment.name!r} costs {cost} "
                f"which is more than available funds ({self.funds})"
            )

        self.units[unit_name] = unit.add_equipment(equipment)
        self.funds = self.funds - cost

    @property
    def cost(self):
        return sum((u.cost for u in self.units.values()), start=Costs())

    def __str__(self):
        lines = [self.name, "=" * len(self.name), ""]
        for name, unit in self.units.items():
            lines.extend(
                [f"{name} ({unit.cost}, {unit.cost.victory_points}vp):", str(unit), ""]
            )

        return "\n".join(lines)


@dataclass
class Unit:
    label: str
    models: CounterList = field(default_factory=CounterList)
    info: Configuration = field(default_factory=Configuration, repr=False)

    #generate info needed to create latex files
    def generate_neat_dict(self, long_=True, format_='tex'):
        translation = {39: None}
        self.neat_dict = {}
        #self.neat_dict['race'] = self.race
        self.neat_dict['models'] = self.models
        self.neat_dict['name'] = self.info.as_dict()['name']
        self.neat_dict['size'] = self.info.size
        try:
            self.neat_dict['cost'] = self.cost
        except AttributeError:
            self.neat_dict['cost'] = 0
            
        try:
            self.neat_dict['armor'] = str(self.info.armor).translate(translation)
        except AttributeError:
            self.neat_dict['armor'] = 0

        txt = ''    
        if format_ =='tex':
            try:
                for u in self.info.special:
                    txt = txt + u + '\\\\ \n'              
            except AttributeError:
                txt = ''
            self.neat_dict['special'] = txt

                
                
        self.neat_dict['victory_points'] = self.cost.victory_points    

        txt = ''
        for key, model  in self.models.as_dict().items():
            #All models of same name should be identical
            #Need only short version in unit section
            
            txt = txt + model[0].write_info(format_=format_, long_=False)

            
        self.neat_dict['models_info'] = txt

        #Generate Order table:
        orders_txt = ''

        if format_ =='tex':        
            with open('ordersheadline_template.tex', 'r') as fid:
                ordersheadline_template = fid.read()

            with open('ordersline_template.tex', 'r') as fid:
                ordersline_template = fid.read()
            
        ordersheadline = ''
        orders = self.info.orders.as_dict()
        for order_name in orders.keys():
            ordersheadline = ordersheadline_template.format(order_name=order_name)
            orderslines = ''
            for speed in orders[order_name].keys():
                for order in orders[order_name][speed]:
                    orderslines = orderslines + ordersline_template.format(speed=speed, order=str(order).translate(translation))
                
            orders_txt = orders_txt + ordersheadline + orderslines

                
        self.neat_dict['orders'] = orders_txt

        #Generate damage tables

        damage_tables_txt = ''

        if format_ =='tex':        
            with open('damage_tableheadline_template.tex', 'r') as fid:
                damage_tablesheadline_template = fid.read()

            with open('damage_tablesline_template.tex', 'r') as fid:
                damage_tablesline_template = fid.read()
        
        damage_tablesheadline = ''
        damage_tables = self.info.damage_tables.as_dict()
        for table_name in damage_tables.keys():
            damage_tablesheadline = damage_tablesheadline_template.format(table_name=table_name)
            damage_tableslines = ''
            for line in damage_tables[table_name]:
                    damage_tableslines = damage_tableslines + damage_tablesline_template.format(line=line)
                
            damage_tables_txt = damage_tables_txt + damage_tablesheadline + damage_tableslines
        
        self.neat_dict['damage_table'] = damage_tables_txt

        
    def write_info(self, long_=True, format_='tex'):
        if format_ == 'tex':
            if long_:
                with open('unit_long.tex', 'r') as fid:
                    unit_long = fid.read()

                self.generate_neat_dict(long_ = True, format_='tex')

                unit_long = unit_long.format(**self.neat_dict)

                with open('long_test.tex', 'w') as fid:
                    fid.write(unit_long)
                
                return unit_long
            
            else:
                with open('unit_short.tex', 'r') as fid:
                    unit_short = fid.read()
                
                self.generate_neat_dict(long_ = False, format_='tex')

                unit_short = unit_short.format(**self.neat_dict)

                with open('short_test.tex', 'w') as fid:
                    fid.write(unit_short)
        
                return unit_short
                  
        
    @classmethod
    def from_toml(cls, unit):
        toml = _all_tomls()
        if unit not in toml.units.section_names:
            units = ", ".join(toml.units.section_names)
            raise ValueError(f"Unknown unit {unit!r}. Use one of {units}")

        unit_cfg = toml.units[unit]
        models = CounterList([Model.from_toml(m) for m in unit_cfg.models])
        return cls(unit, models=models, info=unit_cfg)

    @property
    def equipments(self):
        """List all equipments on unit"""
        return sum((m.equipments for m in self.models), start=CounterList())

    @property
    def cost(self):
        unit_equipment = {
            k: v[0] for m in self.models for k, v in m.equipments.as_dict().items()
        }
        return (
            Costs.from_toml(self.info.get("cost", {}))
            
            + sum((m.added_cost for m in self.models), start=Costs())
            + sum((e.added_unit_cost for e in unit_equipment.values()), start=Costs())
        )

    @property
    def fire_orders(self):
        return self._orders("fire")

    @property
    def movement_orders(self):
        return self._orders("movement")

    def _orders(self, order_type):
        unit_orders = self.info.orders.get(order_type, Configuration()).as_dict()
        for items in (self.models + self.equipments).as_dict().values():
            item = items[0]
            for speed, orders in (
                item.info.get("orders_gained", {}).get(order_type, {}).items()
            ):
                for order in orders:
                    if order not in unit_orders.get(speed, []):
                        unit_orders.setdefault(speed, []).append(order)
        return unit_orders

    @property
    def assault(self):
        return CounterList(m.assault for m in self.models)

    @property
    def range(self):
        return CounterList(m.range for m in self.models)

    def available_upgrades(self, race):
        current_models = set(m.label for m in self.models)
        return {
            k: m
            for k, m in race.models.items()
            if set(m.info.get("replaces", [])) & current_models
        }

    def calculate_model_cost(self, model):
        upgraded_unit = self.upgrade_model(model)
        return upgraded_unit.cost - self.cost

    def upgrade_model(self, replacement_model):
        """Replace one model in the current unit"""
        for idx, current_model in enumerate(self.models):
            if current_model.label in replacement_model.info.get("replaces", []):
                models = self.models[:]
                models[idx] = replacement_model
                return CustomizedUnit(self.label, models=models, info=self.info)

        raise ValueError(
            f"Could not replace {self.models} with {replacement_model.name}"
        )

    def available_equipment(self, race):
        available = {}
        for model in self.models:
            available.update(
                {
                    k: e
                    for k, e in race.equipments.items()
                    if model.allows_equipment(e) and not e.is_free
                }
            )

        return available

    def calculate_equipment_cost(self, equipment):
        upgraded_unit = self.add_equipment(equipment)
        return upgraded_unit.cost - self.cost

    def add_equipment(self, equipment):
        """Add equipment to one model in the current unit"""
        allowed_models = [
            idx for idx, m in enumerate(self.models) if m.allows_equipment(equipment)
        ]
        if not allowed_models:
            raise ValueError(f"Could not add {equipment.name} to {self.models}")

        # Model equipment is only applied to the first allowed model
        if "model_cost" in equipment.info.section_names:
            allowed_models = allowed_models[:1]

        models = self.models[:]
        for idx in allowed_models:
            models[idx] = models[idx].add_equipment(equipment)

        return CustomizedUnit(self.label, models=models, info=self.info)

    @property
    def name(self):
        return self.info["name"]

    def __str__(self):
        lines = []
        for name, model in self.models.as_dict().items():
            lines.append(f"- {len(model)} x {name}: {str(model[0].equipments)}")

        return "\n".join(lines)


class CustomizedUnit(Unit):
    """A unit that has been customized"""


@dataclass
class Model:
    label: str
    equipments: CounterList = field(default_factory=CounterList)
    info: Configuration = field(default_factory=Configuration, repr=False)

    def generate_neat_dict(self, long_ = True, format_ = 'tex'):
        #Translation magic, don't know how it works, but I don't need to.
        translation = {39: None}

        self.neat_dict = {}
        self.neat_dict['race'] = self.info.race
        self.neat_dict['name'] = self.info.as_dict()['name']
        self.neat_dict['type'] = str(self.info.type).translate(translation)
        try:
            self.neat_dict['equipment_limit'] = str(self.info.equipment_limit).translate(translation)
        except:
            self.neat_dict['equipment_limit'] = ''
        try:
            self.neat_dict['cost'] = Costs.from_toml(self.info.cost)
        except AttributeError:
            self.neat_dict['cost'] = ''

            
        self.neat_dict['strength'] = str(self.assault.strength).translate(translation)
        self.neat_dict['strength_die'] = self.assault.strength_die
        self.neat_dict['deflection_die'] = self.assault.deflection_die
        self.neat_dict['deflection'] = str(self.assault.deflection).translate(translation)
        self.neat_dict['assault_ap'] = self.assault.ap
        self.neat_dict['assault_damage'] = self.info.assault.damage

        try:
            replaces = str(self.info.replaces).translate(translation)
            #ToDo: replace replaces (in python name) with name attribute of model it replaces
            self.neat_dict['replaces'] = replaces
        except AttributeError:
            self.neat_dict['replaces'] = 'Nothing'

        try:
            self.neat_dict['cost'] = Costs.from_toml(self.info.cost)
        except:
            self.neat_dict['cost'] = 0
            
        self.neat_dict['equipment'] = self.equipments

        txt = ''
        for key, equipment in self.equipments.as_dict().items():
            #all equipment with same name should be indentical
            #From model we only need the short information.
            txt = txt + equipment[0].write_info(long_=False, format_=format_)

        self.neat_dict['equipment_info'] = txt
            
        txt = ''
        if format_ == 'tex':
            try:
                for u in self.info.assault.special:
                    txt = txt + u + '\\\\ \n'              
            except AttributeError:
                txt = ''
            self.neat_dict['assault_special'] = txt

            txt = ''
            try:
                for u in self.info.special:
                    txt = txt + u + '\\\\ \n'              
            except AttributeError:
                txt = ''
            self.neat_dict['special'] = txt
            
    def write_info(self, long_=True, format_='tex'):
        if format_ == 'tex':
            if long_:
                with open('model_long.tex', 'r') as fid:
                    model_long = fid.read()

                self.generate_neat_dict(long_ = True, format_='tex')

                model_long = model_long.format(**self.neat_dict)

                return model_long
            
            else:
                with open('model_short.tex', 'r') as fid:
                    model_short = fid.read()
                
                self.generate_neat_dict(long_ = False, format_='tex')

                model_short = model_short.format(**self.neat_dict)

                return model_short
            


    
    @classmethod
    def from_toml(cls, model):
        toml = _all_tomls()
        if model not in toml.models.section_names:
            models = ", ".join(toml.models.section_names)
            raise ValueError(f"Unknown model {model!r}. Use one of {models}")

        model_cfg = toml.models[model]
        equipments = CounterList(
            [Equipment.from_toml(e) for e in model_cfg.get("equipments", [])]
        )
        return cls(model, equipments=equipments, info=model_cfg)

    @property
    def added_cost(self):
        return Costs.from_toml(self.info.get("cost", {})) + sum(
            (e.added_model_cost for e in self.equipments), start=Costs()
        )

    def remaining_equipment_limits(self, equipments=None, ignore_free_equipment=True):
        equipments = self.equipments if equipments is None else equipments
        limits = parse_requirements(self.info.equipment_limit)
        for equipment in equipments:
            # Don't count free equipment
            if ignore_free_equipment and equipment.is_free:
                continue

            for requirement_strings in equipment.info.requires:
                requirement = parse_requirements(requirement_strings)
                for attribute, value in requirement.items():
                    if attribute in limits:
                        limits[attribute] -= value

        return limits

    def equipment_overflow(self, equipments=None, ignore_free_equipment=True):
        return any(
            limit < 0
            for limit in self.remaining_equipment_limits(
                equipments, ignore_free_equipment=False
            ).values()
        )

    def allows_equipment(self, equipment):
        # Check each requirement of the equipment
        
        for requirement_strings in equipment.info.requires:
            requirement = parse_requirements(requirement_strings, as_list=True)
            for attribute, allowed_values in requirement.items():
                if attribute in self.info.entry_keys:
                    
                    
                    value = (
                        [self.info[attribute]]
                        if isinstance(self.info[attribute], str)
                        else self.info[attribute]
                    )
                    if not set(value) & set(allowed_values):
                        return False
                else:
                    value = allowed_values[0]
                    if value > self.remaining_equipment_limits().get(attribute, 0):
                        return False
        return True

    def add_equipment(self, equipment):
        """Add equipment to model, remove free equipment if necessary"""
        equipments = self.equipments[:]
        equipments.append(equipment)

        while self.equipment_overflow(
            equipments=equipments, ignore_free_equipment=False
        ):
            for idx, current_equipment in enumerate(equipments):
                if not current_equipment.is_free:
                    continue
                equipments.pop(idx)
                break

        return CustomizedModel(self.label, equipments=equipments, info=self.info)

    @property
    def assault(self):
        stats = AssaultStats.from_cfg(
            self.name, self.info.get("assault", Configuration())
        )
        for equipment in self.equipments:
            stats = stats.update_from_cfg(
                equipment.info.get("assault", Configuration())
            )
        return stats

    @property
    def range(self):
        """TODO"""
        stats = RangeStats.from_cfg(self.name, self.info.get("range", Configuration()))
        for equipment in self.equipments:
            stats = stats.update_from_cfg(equipment.info.get("range", Configuration()))
        return stats

    @property
    def name(self):
        return self.info["name"]

    def __str__(self):
        return self.name


class CustomizedModel(Model):
    """A model that has been customized"""


@dataclass
class Equipment:
    label: str
    info: Configuration = field(default_factory=Configuration, repr=False)

    def generate_neat_dict(self, long_=True, format_='tex'):
        translation = {39: None}
        self.neat_dict = {}
        self.neat_dict['race'] = self.info.race
        self.neat_dict['name'] = self.info.as_dict()['name']
        if long_:
            self.neat_dict['requiers'] = str(self.info.requires).translate(translation)
        

        try:
            self.neat_dict['cost'] = 'Upgrade all models for: ' + str(Costs.from_toml(self.info.cost))
        except AttributeError:
            try:
                self.neat_dict['cost'] = 'Upgrade one model for: ' + str(Costs.from_toml(self.info.model_cost))
            except AttributeError:
                self.neat_dict['cost'] = 0
        
            
        try:
            self.info.range
            ranged = True
        except AttributeError:
            ranged = False

        self.neat_dict['ranged'] = ranged

        try:
            special = self.info.special
        except AttributeError:
            special = []

        txt = ''
        if format_ == 'tex':
            for s in special:
                txt = txt + s + '\\\\ \n'

        self.neat_dict['special'] = txt
                
        if format_ =='tex':        
            with open('ordersheadline_template.tex', 'r') as fid:
                ordersheadline_template = fid.read()

            with open('ordersline_template.tex','r') as fid:
                ordersline_template = fid.read()
            
        ordersheadline = ''
        orders_txt = ''
        try:
            orders = self.info.orders_gained.as_dict()
        except AttributeError:
            orders = {}
            
        for order_name in orders.keys():
            ordersheadline = ordersheadline_template.format(order_name=order_name)
            orderslines = ''
            for speed in orders[order_name].keys():
                for order in orders[order_name][speed]:
                    orderslines = orderslines + ordersline_template.format(speed=speed, order=str(order).translate(translation))
                
            orders_txt = orders_txt + ordersheadline + orderslines

        self.neat_dict['orders'] = orders_txt

        txt = ''
        if ranged:
            self.neat_dict['range'] = self.info.range.range
            self.neat_dict['angle'] = self.info.range.angle
            self.neat_dict['ranged_ap']  = self.info.range.ap
            self.neat_dict['ranged_damage'] = self.info.range.damage
            
            
            if format_ =='tex':
                for s in self.info.range.special:
                    txt  = txt + s + '\\\\ \n'              

        self.neat_dict['range_special']  = txt



        try:
            self.info.assault
            assault_weapon = True
        except AttributeError:
            assault_weapon = False

        self.neat_dict['assault_weapon'] = assault_weapon


        self.neat_dict['assault_special'] = ''
        self.neat_dict['assault_headline'] = ''
        if assault_weapon:
            self.neat_dict['assault_headline'] = 'Assault \\\\'
            txt = ''
            self.assault_neat_dict = {}
            try:
                self.neat_dict['strength'] = self.info.assault.strength.add
                
            except AttributeError:
                pass

            
            try:
                self.neat_dict['deflection'] = self.info.info.assault.deflection.add
                self.neat_dict['deflection_die'] = self.info.info.assault.deflection_die.replace
            except AttributeError:
                pass

            try:
                self.neat_dict['assault_damage'] = self.info.assault.damage.replace
            except AttributeError:
                pass

            try:
                self.neat_dict['ap'] = self.info.assault.ap.replace
            except AttributeError:
                pass

            try:
                assaultspecials = self.info.assault.special
            except AttributeError:
                assaultspecials = []

            txt = ''
            if format_ =='tex':
                for a in assaultspecials:
                    txt = txt + a + '\\\\ \n'
            self.neat_dict['assault_special'] = txt


            
    def write_info(self, long_=True, format_='tex'):
        if format_ == 'tex':
            if long_:
                with open('equipment_long.tex', 'r') as fid:
                    equipment_long = fid.read()
                
                    
                self.generate_neat_dict(long_ = True, format_='tex')

                assault = ''
                if 'assault_strength' in self.neat_dict.keys():
                    if format=='tex':
                        with open('assault_strength.tex', 'r') as fid:
                            assault_strength = fid.read()
                        assault = assault_strength.format(**self.neat_dict) + '\\\\ \n'
                if 'assault_damage' in self.neat_dict.keys():
                    if format=='tex':
                        with open('assault_damage.tex', 'r') as fid:
                                assault_damage = fid.read()
                        assault = assault + assault_damage.format(**self.neat_dict) + '\\\\ \n'

                if 'assault_ap' in self.neat_dict.keys():
                    if format=='tex':
                        with open('assault_ap.tex', 'r') as fid:
                            assault_ap = fid.read()
                        assault = assault + assault_ap.format(**self.neat_dict) + '\\\\ \n'

                if 'assault_deflection' in self.neat_dict.keys():
                    if format=='tex':
                        with open('assault_ap.tex', 'r') as fid:
                            assault_ap = fid.read()
                        assault = assault + assault_ap.format(**self.neat_dict) + '\\\\ \n'

                equipment_ranged = ''
                if self.neat_dict['ranged']:
                    with open('equipment_ranged.tex', 'r') as fid:
                        equipment_ranged = fid.read()
                        

                        
                self.neat_dict['range'] = equipment_ranged.format(**self.neat_dict)
                        
                self.neat_dict['assault'] = assault
                        
                equipment_long = equipment_long.format(**self.neat_dict)

                return equipment_long
            
            else:
                with open('equipment_short.tex', 'r') as fid:
                    equipment_short = fid.read()
                
                self.generate_neat_dict(long_ = False, format_='tex')

                equipment_ranged = ''
                if self.neat_dict['ranged']:
                    with open('equipment_ranged.tex', 'r') as fid:
                        equipment_ranged = fid.read()
                    
                self.neat_dict['range'] = equipment_ranged.format(**self.neat_dict)
                
                equipment_short = equipment_short.format(**self.neat_dict)

                return equipment_short

        
    @classmethod
    def from_toml(cls, equipment):
        toml = _all_tomls()
        if equipment not in toml.equipments.section_names:
            equipments = ", ".join(toml.equipments.section_names)
            raise ValueError(
                f"Unknown equipment {equipment!r}. Use one of {equipments}"
            )

        equipment_cfg = toml.equipments[equipment]
        return cls(equipment, info=equipment_cfg)

    @property
    def name(self):
        return self.info["name"]

    @property
    def is_free(self):
        return not {"cost", "model_cost"} & set(self.info.section_names)

    @property
    def added_unit_cost(self):
        return Costs.from_toml(self.info.get("unit_cost", {}))

    @property
    def added_model_cost(self):
        return Costs.from_toml(self.info.get("model_cost", {}))

    def __str__(self):
        return self.name


@dataclass
class Stats:
    """Common methods for Stats classes"""

    name: str

    @classmethod
    def from_cfg(cls, name, cfg):
        return cls(name=name, **cfg)

    def update_from_cfg(self, cfg):
        values = self.__dict__.copy()
        for name, operation in cfg.section_items:
            if "add" in operation:
                if isinstance(values[name], list):
                    values[name] = [
                        v + n for v, n in zip(values[name], operation["add"])
                    ]
                else:
                    values[name] += operation["add"]
            elif "replace" in operation:
                values[name] = operation["replace"]
            elif "append" in operation:
                values[name].append(operation["append"])

        return self.__class__(**values)


@dataclass
class AssaultStats(Stats):
    strength: list
    strength_die: str
    deflection: list
    deflection_die: str
    damage: str
    ap: int
    special: list


@dataclass
class RangeStats(Stats):
    range: int
    angle: list
    damage: str
    ap: int
    special: list


def all_races():
    toml = _all_tomls()
    return {race: Race.from_toml(race) for race in toml.races.section_names}


@functools.lru_cache
def _all_tomls():
    file_paths = pathlib.Path(__file__).parent.glob("*.toml")
    toml = Configuration()
    for path in file_paths:
        print(path)
        toml.update_from_file(path)

    return toml


def parse_requirements(requirement_strings, as_list=False):
    requirements = {}
    for requirement in requirement_strings:
        item, _, value = requirement.partition(":")
        model_or_unit, _, attribute = item.rpartition(".")

        # Interpret value as number if possible
        try:
            value = int(value)
        except ValueError:
            pass
        if value == "∞":
            value = float("inf")

        item = (
            requirements.setdefault(model_or_unit, {})
            if model_or_unit
            else requirements
        )
        if as_list:
            item.setdefault(attribute, []).append(value)
        else:
            item[attribute] = value

    return requirements

