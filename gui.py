
import dash
import dash_html_components as html
import dash_core_components as dcc

import armybuilder



app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Dropdown(options=[
        {'label': 'DarkElf', 'value': 'DarkElf'},
        {'label': 'Elf', 'value': 'Elf'},
        {'label': 'Dwarf', 'value': 'Dwarf'},
        {'label': 'Ork', 'value': 'Ork'},
        {'label': 'Gnome', 'value': 'Gnome'},
        
    ],
                
                 value='', id='team', placeholder="Select a team"),

        dcc.Dropdown(options=[
    ],
                
                     value='', id='unit', placeholder="Select a unit"),


    dcc.Dropdown(options=[
    ],
                
                 value='N.A', id='upgrades', placeholder="Select a upgrade if any"),


    
    html.Div(id='output-container',
             children='Choose A team.')
    
])


@app.callback(
    dash.dependencies.Output('output-container', 'children'),
    [dash.dependencies.Input('team', 'value')])
def update_output(value):
    return 'The team chosen is {}'.format(
        value
        
    )


@app.callback(
    dash.dependencies.Output('unit', 'options'),
    [dash.dependencies.Input('team', 'value')])
def update_output(value):
    global team
    team = armybuilder.Team(value)
    try:
        team.from_toml()
        chooseUnit = []
        for unitname, unit in team.units.items():
            chooseUnit.append({'label' : unitname, 'value': unitname})
    except FileNotFoundError:
        chooseUnit = []
        
    

    return chooseUnit



@app.callback(
    dash.dependencies.Output('upgrades', 'options'),
    [dash.dependencies.Input('unit', 'value')])
def update_output(unitname):

    options = []
    
    if unitname:
        upgrades_possible = team.upgrades(team.units[unitname])
        
        for upgrades in upgrades_possible.keys():
            options.append({'label' : upgrades, 'value':upgrades})

    print(options)
    return options
        
    


if __name__ == '__main__':
    app.run_server(debug=True)

