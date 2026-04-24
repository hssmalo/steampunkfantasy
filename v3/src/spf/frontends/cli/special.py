"""Army commands for the SteamPunkFantasy CLI."""

import pathlib

import cyclopts

from spf import races
from spf.armies import io
from spf.config import config
from spf.console import stderr, stdout


def add_commands(app: cyclopts.App) -> None:
    """Add special commands to the CLI."""
    app.command(show_special, name="show")

    
#To Do: put it in another place
possible_races = ['elf','darkelf','abomination', 'goblin', 'ogre', 'ork']

def show_special(special_key: str) -> None:
    for race_name in possible_races:
        race = races.get_race(race_name)
        
        #To Do: Stor bokstav på race navnene...
        stdout.print(f"{race_name}")
        for unit_name,unit in race.units.items():
            for k in unit.special.keys(): 
                if k == special_key:
                    stdout.print(f"Unit: {unit.name:<30}  {special_key: <24} {unit.special[special_key]:<100}", highlight=False)

        for model_name,model in race.models.items():
            for k in model.special.keys(): 
                if k == special_key:
                    stdout.print(f"Model: {model.name:<30}  {special_key: <24} {model.special[special_key]:<100}", highlight=False)
            for k in model.unit_special.keys(): 
                if k == special_key:
                    stdout.print(f"Model: {model.name:<30}  {special_key: <24} {model.unit_special[special_key]:<100}", highlight=False)
            for k in model.assault.special.keys():
                if k == special_key:
                    stdout.print(f"Model: {model.name:<30}  {special_key: <24} {model.assault.special[special_key]:<100}", highlight=False)
    

        for equipment_name,thing in race.equipment.items():
            for k in thing.unit_special.keys(): 
                if k == special_key:
                    stdout.print(f"Equipment: {equipment.name:<30}  {special_key: <24} {thing.unit_special[special_key]:<100}", highlight=False)

            for k in thing.model_special.keys(): 
                if k == special_key:
                    stdout.print(f"Equipment: {equipment.name:<30}  {special_key: <24} {thing.model_special[special_key]:<100}", highlight=False)

            if thing.assault:
                for k in thing.assault.special.keys(): 
                    if k == special_key:
                        stdout.print(f"Equipment: {equipment.name:<30}  {special_key: <24} {thing.assault.special[special_key]:<100}", highlight=False)
