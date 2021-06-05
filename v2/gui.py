
import dash
import dash_html_components as html
import dash_core_components as dcc

from data import Costs
from data import Race
from data import Team

#from copy import deepcopy


import data

TEAM = None
FUNDS = None
RACE = None
UNIT = None



app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div(id='game', children='SteamPunkFantazy'), 
    
    html.Div(id='funds',
             children='Left FUNDS = '),

    dcc.Input(id='teamname', type = 'text', placeholder = "Enter personalised team name."),

    
    html.Button('Save Name', id='submit_name', n_clicks=0),  
    
    dcc.Dropdown(options = [{'label': 'Standar', 'value': '24ip, 24mp, 24xp, 24cp'}], id ='gametype', placeholder ='Choose a game type'),
    
    dcc.Dropdown(options=[{'label' : 'Dark Elf', 'value': 'darkelf'}, {'label': 'Ork', 'value': 'ork'}], id='race', placeholder="Select a race"),


    dcc.Dropdown(options=[{'label' : 'New Unit', 'value': 'new'}, {'label': 'Modify unit', 'value':'modify'}],
                
                 value='new', id='newORmodify'),

    

    dcc.Dropdown(options=[],
                
                     value='', id='unitname', placeholder="Select a unit"),


    dcc.Dropdown(options=[],
                
                 value='N.A', id='modelupgrade', placeholder="Upgrade a model if possible"),
    

    dcc.Dropdown(options=[],
                
                 value='N.A', id='equipmentupgrade', placeholder="Select a upgrade if any"),



    html.Button('Save', id='save', n_clicks=0),  

    
    html.Div(id='output',
             children='')
    
])


@app.callback(
    dash.dependencies.Output('game', 'children'),
    dash.dependencies.Output('funds', 'children'),
    [dash.dependencies.Input('gametype', 'value')]
)
def update_FUNDS(gametype):

       
    if gametype is not None:
        global FUNDS
        FUNDS = Costs.from_string(gametype)

        if TEAM:
            TEAM.funds = FUNDS
        
        
    return 'SteamPunkFantazy', 'Starting Funds :' + str(FUNDS)




@app.callback(
    dash.dependencies.Output('unitname', 'options'),
    [dash.dependencies.Input('race', 'value'),
    dash.dependencies.Input('newORmodify', 'value'),
    ]
)

def update_units(race, newORmodify):

    print('updating units')
    global RACE
    options = []
    if newORmodify == 'new':    
        
        if race:
            RACE = Race.from_toml(race)

    
            for unitpythonname, unit in RACE.units.items():
                entry = {'label': unit.name, 'value': unitpythonname}
                options.append(entry)

    else:
        for unitpythonname, unit in TEAM.units.items():
                entry = {'label': unit.name, 'value': unitpythonname}
                options.append(entry)
        
                
    return options


@app.callback(
    dash.dependencies.Output('teamname', 'value'),
    [dash.dependencies.Input('submit_name', 'n_clicks'),
     dash.dependencies.State('teamname', 'value'),
    ]
)
def update_team(n_clicks, teamname):

    print('updating team')
    global TEAM
    TEAM = Team(teamname)

    return teamname


@app.callback(
    dash.dependencies.Output('modelupgrade', 'options'),
    dash.dependencies.Output('equipmentupgrade', 'options'),
    [dash.dependencies.Input('unitname', 'value'),
     dash.dependencies.State('newORmodify', 'value'),
    ]
)
def update_upgrades(unitname, newORmodify):
    print('upgrading upgrade options')
    
    model_options = []
    equipment_options = []

    if newORmodify == 'modify':
        print('hei hei')
        if RACE is not None:
            print('Race is not none')
            if TEAM is not None:
                print('team is not none')
                print(TEAM.name)
                all_models = TEAM.units[unitname].available_upgrades(RACE)
                all_eq = TEAM.units[unitname].available_equipment(RACE)

                model_options = []
                for modelname, model in all_models.items():
                    entry = {'label': modelname, 'value': modelname}
                    model_options.append(entry)


                equipment_options = []
                for equipmentname, equipment in all_eq.items():
                    entry = {'label': equipmentname, 'value': equipmentname}
                    equipment_options.append(entry)

        
                
    return model_options, equipment_options


@app.callback(
    dash.dependencies.Output('output', 'children'),
    [dash.dependencies.Input('save', 'n_clicks'),
     dash.dependencies.State('newORmodify', 'value'),
     dash.dependencies.State('unitname', 'value'),
     dash.dependencies.State('modelupgrade', 'value'),
     dash.dependencies.State('equipmentupgrade', 'value'),
    ]
)
def save(n_clicks, newORmodify, unitname, modelname, equipmentname):

    print('Saving')
    funds = ''
    if newORmodify == 'new':
        if RACE is not None:
        
            if TEAM is not None:
                TEAM.add_unit(RACE.units[unitname])
                funds = str(TEAM.funds)
            
    if newORmodify == 'modify':
        if RACE is not None:
            if TEAM is not None:
                TEAM.upgrade_model(unitname, RACE.models[modelname])
                TEAM.add_equipment(unitname, RACE.equipments[equipmentname] )
                funds = str(TEAM.funds)
                                   
    return 'Funds Left:' + funds





    

if __name__ == '__main__':
    app.run_server(debug=True)

