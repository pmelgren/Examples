import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL
import plotly.express as px
import numpy as np
import pandas as pd
import glob

#######################
# Helper functions
#######################

# convert a dataframe into a dict where each item is another dict corresponding
# to a row of the html table
def make_table(dfs):
    
    # table header
    rows = [html.Tr([html.Th('Filename'),html.Th('')])]
    
    # loop through each unique filename and create a list of the Html objects to make that row
    for i,f in enumerate(dfs.loc[dfs.display == True,'Filename'].unique()):
        
        # add the filename to the row with coloring 
        colornum= 255/(len(dfs.loc[dfs.display == True,'Filename'].unique()))*(i+1)
        row = [html.Th(f,style = {'color':'rgb('+str(colornum)+',100,'+str(255-colornum)+')'})]                
        # add an html button to remove the file data 
        row.append(html.Button('Remove File Data', n_clicks=0
                               ,id = {'type': 'table-button', 'value': f}))
        rows.append(html.Tr(row))
    return(rows)

# create the plot of the Velocity grouped by Frequency
def make_plot(dfs):
    grouped = dfs.groupby('Frequency').mean()['Velocity'] # get mean velocity grouped by freq
    graph = px.scatter(grouped.reset_index(),x='Velocity',y='Frequency') # create a graph 
    return graph


#######################
# Initial Data Prep
#######################

# get all files in the CWD
filelist = glob.glob("*.fv")

# loop through each file read in the relevant data and add to a dataframe
df = pd.DataFrame() # create the global df that will contain all the data
for file in filelist:
    # make the next file a data frame
    fdf = pd.read_csv(file,skiprows=23,skipfooter=5, delimiter=' '
                      , names=['Frequency','Velocity'])
    fdf['Filename'] = file
    
    # add the file df to the global df
    df = df.append(fdf).reset_index(drop = True)
    
# sort by Frequency and reset index.
df = df.sort_values('Frequency', ascending = True).reset_index(drop = True)
df['display'] = True # column to indicate if the row will be displayed


#######################
# Dash app layout
#######################
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

# put the table of the sorted data in the left half of the screen
leftpanel = [
    html.Table(make_table(df),id='sorted-table',className='table')
]

# put the graph in the right half of the screen
rightpanel = dbc.Card([
    dcc.Graph(id='averaged-by-freq',figure = make_plot(df))
    
    # create a hidden object to store the data as it changes (this is useful for reactivity purposes)
    ,html.Div(df.to_json(),id='intermediate-value',style={'display': 'none'})
])

# lay out the app based on the above panel definitions
app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(leftpanel, md=6),
            dbc.Col(rightpanel, md=6)
        ])
],fluid=True)


#######################
# Reactive callbacks
#######################

# When any of the buttons are clicked read the data in the hidden Div object
# into a DataFrame, then remove all rows that have the filename associated with
# the button that was clicked
@app.callback(
    Output('intermediate-value','children')
    ,[Input({'type': 'table-button', 'value': ALL}, 'n_clicks')]
    ,[State('intermediate-value','children')]
)
def update_data(clicks,json_dat):
    # clicks is a list of numbers representing each button in the table. The one that was clicked should be 1
    if sum(clicks) > 0:
        ddf = pd.read_json(json_dat) # create a dataframe out of the data in the hidden Div
        ddf = ddf.loc[ddf.display == True,:] #remove rows not displayed and reset index
        files_to_hide = ddf.Filename.unique()[np.array(clicks) > 0]
        ddf.loc[ddf.Filename.isin(files_to_hide),'display'] = False # set display to false for the filenames to hide
        return ddf.to_json() # write the updated data back to the hidden Div object
    else:
        return json_dat
    
# when the data in the hidden Div changes, update the figure based on the rows
# where display is True
@app.callback(
    Output('averaged-by-freq','figure')
    ,[Input('intermediate-value', 'children')]
)
def update_plot(dat):
    cdf = pd.read_json(dat) # create a dataframe out of the data in the hidden Div
    cdf = cdf.loc[cdf.display == True,:] # keep only rows where display is True
    return make_plot(cdf) # return the plot based on the updated data

# when the data in the hidden Div changes, update the table based on the rows
# where display is True
@app.callback(
    Output('sorted-table','children')
    ,[Input('intermediate-value', 'children')]
)
def update_table(dat):
    tdf = pd.read_json(dat) # create a dataframe out of the data in the hidden Div
    tdf = tdf.loc[tdf.display == True,:] # keep only rows where display is True
    return make_table(tdf) # create a new table based on the updated data

# necessary code at the bottom of all Dash apps to run the app
if __name__ == "__main__":
    app.run_server(debug=False, port = 8050)
