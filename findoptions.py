from data import Team
from data import Costimized_unit



def find_possible_items(costimized_unit, team):

    for weapon_name,weapon in team.weapons.items():
        #print(weapon_name)
        if weapon.cost == '':
            continue
        tmp = weapon.required_to_buy.split(':')
        
        modelORunit = tmp[0]
        required = tmp[1].split(' or ')

        
        types = [a.strip().lower() for a in costimized_unit.type_.split(',')]
        types.append(costimized_unit.baseunitname.strip().lower())
        
        ##check if unit meets the requirements of the item.
        for r in required:
            still_true = True
            #print(weapon.name)
            #print(r)
            #print(types)
            if r.strip().lower() not in types:
                    still_true = False

            #print(still_true)
            if still_true:
                break 

        #print(still_true)
            
        if not still_true:
            continue

        handed = ['1handed weapon', '2handed weapon', '3handed weapon', '4handed weapon']
        hands = ['1 hands', '2 hands', '3 hands', '4 hands']

        ##check if the weapon meets the requirements of the unit.
        unit_items = costimized_unit.unititems.split(',')
        type_ = weapon.type_.split(',')[1]
        type_ = type_.lower().strip()
        
        #print(still_true)



        modified_unit_items = []
        for u in unit_items:
            tmp = u.strip()
            tmp = tmp[1:]
            tmp = tmp.strip()
            
            modified_unit_items.append(tmp)

            
        #print(type_.strip().lower(), modified_unit_items)
            
        if not type_ in modified_unit_items:
            still_true = False

        ###Works so far!!!

        #print('1', weapon.name)
        if not still_true:
            still_true = True
            if int(costimized_unit.models) > 0:
                model_items = costimized_unit.modelitems.split(',')
                model_items = [a.lower().strip() for a in model_items]
                mod = []
                for m in model_items:
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
                                #print('fuck')
                                numberof_modelhands = int(m[0])

                        
                        if numberofhands_required > numberof_modelhands:
                            still_true = False
                        #print(still_true)
                            
                for replacement_name, replacement in costimized_unit.replacements.items():
                    still_true = ture
                    
                    model_items = replacement.modelitems.split(',')
                    model_items = [a.lower().strip() for a in model_items]
                    mod = []
                    for m in model_items:
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

                                
        if still_true:
            print(weapon_name)



import IPython; IPython.embed()
