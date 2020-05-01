from data import Team
from data import costimized_unit



def find_possible_items(costimized_unit, team):

    for weapon_name,weapon in team.weapons.itmes:
        if weapon.cost = '':
            continue
        tmp = weapon.requiered_to_buy.split(':')
        modelORunit = tmp[0]
        required = tmp[1].split('or')

        ##check if unit meets the requirements of the item.
        for i in required:
            still_true = True
            if i not in costimized_unit.type_:
                    still_true = False
                    
            if still_true:
                break

        if not still_true:
            break

        handed = ['1handed', '2handed', '3handed', '4handed']
        ##check if the weapon meets the requirements of the unit.
        unit_items = costimized_unit.unititems.split(',')
        type_ = weapon.type.split(',')[1]
        
        if not type_ in unit_items:
            still_true = False

        if costimized_unit.models > 0:
            model_items = costimized_unit.modelitems.split(',')
            if not type_ in model_items:
                if type_ in handed:
                    numberofhands_required = int(type_[0])
                    numborof_modelhands  = 0
                    for m in model items:
                        if m in handed:
                            numberof_modelhands = int(m[0])

                        

                    if numberofhands_requiered > numberof_modelhands:
                        still_true = False
                        
         for replacement_name, replacement in costimized_unit.replacements.items():
             model_items = replacement.modelitems.split(',')
             if not type_ in model_items:
                 if type_ in handed:
                     numberofhands_required = int(type_[0])
                     numborof_modelhands  = 0
                     for m in model items:
                         if m in handed:
                             numberof_modelhands = int(m[0])

                        

                    if numberofhands_requiered > numberof_modelhands:
                        still_true = False
 
                
                
        if still_true:
            print(weapon_name)
