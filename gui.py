
import dash
import dash_html_components as html
import dash_core_components as dcc



import armybuilder
import build

TEAM = None
FUNDS = None




app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div(id='game', children='SteamPunkFantazy'), 
    
    html.Div(id='funds',
             children='Left FUNDS = '),
    
    dcc.Dropdown(options = [], id ='gametype', placeholder ='Choose a game type'),
    
    dcc.Dropdown(options=[],
                
                 value='', id='team', placeholder="Select a team"),

    dcc.Dropdown(options=[],
                
                     value='', id='unitname', placeholder="Select a unit"),


    dcc.Dropdown(options=[],
                
                 value='N.A', id='upgradename', placeholder="Select a upgrade if any"),


    dcc.Dropdown(options=[{'label' : 'New Unit', 'value': 'new'}, {'label': 'Modify unit', 'value':'modify'}],
                
                 value='new', id='newORmodify'),




    
    dcc.Input(id='personalname', type = 'text', placeholder = "Enter personalised unit name. Must be a unique name for each unit"),

    html.Button('Save', id='submit', n_clicks=0),  
              
    html.Div(id='output-container',
             children='Choose A team.')
    
])


@app.callback(
    dash.dependencies.Output('output-container', 'children'),
    dash.dependencies.Output('team', 'options'),
    dash.dependencies.Output('gametype', 'options'),
    dash.dependencies.Output('funds', 'children'),
    
    [dash.dependencies.Input('submit', 'n_clicks')],
    [dash.dependencies.State('newORmodify', 'value')],
    [dash.dependencies.State('unitname', 'value')],
    [dash.dependencies.State('upgradename', 'value')],
    [dash.dependencies.State('personalname', 'value')],
    
)
def update_output(n_clicks, newORmodify, unitname, upgradename, personalname):
    upgrade = ''
    cost = ''
    global FUNDS
    
    if unitname:
        if newORmodify == 'new':
            unit = TEAM.units[unitname]
        if newORmodify == 'modify':
            try:
                unit = TEAM.personal_team[unitname]
            except:
                unit = None

        if unit is not None:
            try:    
                upgrade = TEAM.upgrades(unit)[upgradename]
            except KeyError:
                upgrade = ''

        if newORmodify == 'new':
            cost = build.Costs.from_string(unit.cost)
            
                
        if upgrade not in ['', 'nothing']:
            unit.add_equipment(upgrade)
            if newORmodify == 'new':
                cost = cost + build.Costs.from_string(upgrade.cost)
            if newORmodify == 'modify':
                cost = build.Costs.from_string(upgrade.cost)
            


        if FUNDS is not None:
            
            FUNDS = FUNDS - cost
            
            TEAM.personal_team[personalname] = unit

            txt = 'Unit Name: {},Upgrade Name {},Personal Name {}'.format(unitname, upgradename, personalname)

            showfunds = str(FUNDS)
            
        options_team = [{'label' : TEAM.name, 'value': TEAM.name}]
        options_gametype = [] 

        
    else:
        txt = 'Once the save new button is pressed, you can no longer change team after you have pushed the save new button'

        showfunds = 'Choose a gametype to see what funds you will get'
        
        options_team = [
            {'label': 'DarkElf', 'value': 'DarkElf'},
            {'label': 'Elf', 'value': 'Elf'},
            {'label': 'Dwarf', 'value': 'Dwarf'},
            {'label': 'Ork', 'value': 'Ork'},
            {'label': 'Gnome', 'value': 'Gnome'}]

        options_gametype = [{'label': a + ' ' + b, 'value': b} for a,b in build.ARMIES.items()]
        
    return txt, options_team, options_gametype, showfunds



@app.callback(
    dash.dependencies.Output('unitname', 'options'),
    dash.dependencies.Output('unitname', 'value'),
    [dash.dependencies.Input('team', 'value')],
    [dash.dependencies.Input('newORmodify', 'value')],
)
def update_unitnames(team, newORmodify):
    chooseUnit = []
    unitname = ''
    if newORmodify == 'new':
        global TEAM
        TEAM = armybuilder.Team(team)
        try:
            TEAM.from_toml()
            for unitname, unit in TEAM.units.items():
                chooseUnit.append({'label' : unitname, 'value': unitname})
        except FileNotFoundError:
            chooseUnit = []
        
            
    if newORmodify == 'modify':
        #print(TEAM.personal_team)
        for unitname, unit in TEAM.personal_team.items():
            chooseUnit.append({'label': unitname, 'value': unitname})

    if chooseUnit:
        unitnname = chooseUnit[0]

            
    return chooseUnit, unitname



@app.callback(
    dash.dependencies.Output('game', 'children'),
    [dash.dependencies.Input('gametype', 'value')]
)
def update_FUNDS(gametype):

    if gametype is not None:
        global FUNDS
        FUNDS = build.Costs.from_string(gametype)
    
    return 'SteamPunkFantazy'


    
@app.callback(
    dash.dependencies.Output('upgradename', 'options'),    
    [dash.dependencies.Input('unitname', 'value')],
    [dash.dependencies.Input('submit', 'n_clicks')],
    [dash.dependencies.State('newORmodify', 'value')]
)
def update_upgrades(unitname, n_clicks, newORmodify):

    options = [{'label': 'nothing', 'value': 'nothing'}]
    print(unitname, newORmodify, n_clicks)
   
    
    if unitname and TEAM is not None:
        if newORmodify == 'new':
            unit = TEAM.units[unitname]
        if newORmodify == 'modify':
            unit = TEAM.personal_team[unitname]

        if unit is not None:
            upgrades_possible = TEAM.upgrades(unit)
        
            
            for upgrades in upgrades_possible.keys():
                options.append({'label' : upgrades, 'value':upgrades})
        else:
            options = []
                
    print(options)
    return options
        
    


if __name__ == '__main__':
    app.run_server(debug=True)

