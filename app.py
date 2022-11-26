from dash.dependencies import Input, Output
from cs50 import SQL
from dash import Dash, html, dash_table, dcc, ctx
import plotly.express as px
import pandas as pd
import os
import plotly.graph_objects as go

from helpers import generate_graph, generate_table, add_traces_to_fig, diff_set, add_trace_to_fig, reload_data_from_db

# Path to database created in EMC Plotter DB
db_name = 'plotter.db'
path_to_emc_plotter_db = '/home/ilya.s/EMC_Plotter_DB.git/cs50_final_project/'

# App layout
app = Dash(__name__, prevent_initial_callbacks=True)

# Create variables to store callback variables (declared as global in the callback function)
dff = pd.DataFrame()
slctd_rows_prev = []
fig = go.Figure()

# Connect to plotter.db and read  it into a dataframe
df = reload_data_from_db(path_to_emc_plotter_db + db_name)

# Sorting operators (https://dash.plotly.com/datatable/filtering)
app.layout = html.Div([html.Div(id='line-container'),
    dash_table.DataTable(
        id='datatable-interactivity',
        columns=[
            {"name": i, "id": i, "deletable": True, "selectable": True, "hideable": True}
            if i == "username" or i == "timestamp" or i == "name" or i == "description" or i == "folder" or i == "filename" or i == "lab"
            else {"name": i, "id": i, "deletable": True, "selectable": True}
            for i in df.columns
        ],
        data=df.to_dict('records'),  # the contents of the table
        hidden_columns = ["folder", "filename"],
        editable=False,              # allow editing of data inside all cells
        filter_action="native",     # allow filtering of data by user ('native') or not ('none')
        sort_action="native",       # enables data to be sorted per-column by user or not ('none')
        sort_mode="single",         # sort across 'multi' or 'single' columns
        column_selectable=False,  # allow users to select 'multi' or 'single' columns
        row_selectable="multi",     # allow users to select 'multi' or 'single' rows
        row_deletable=False,         # choose if user can delete a row (True) or not (False)
        selected_columns=[],        # ids of columns that user selects
        selected_rows=[],           # indices of rows that user selects
        page_action="native",       # all data is passed to the table up-front or not ('none')
        page_current=0,             # page number that user is on
        page_size=20,                # number of rows visible per page
        style_header={
            'backgroundColor': 'rgb(210, 210, 210)',
            'color': 'black',
            'fontWeight': 'bold'
        },  
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(220, 220, 220)',
            }
        ],
        style_cell={                # ensure adequate header width when text is shorter than cell's text
            'maxWidth': 0, 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'textAlign': 'left'
        },
        style_cell_conditional=[
            {'if': {'column_id': 'comment'},
            'width': '15%'},
            {'if': {'column_id': 'description'},
            'width': '15%'},
        ],
        #style_data={                # overflow cells' content into multiple lines
            #'whiteSpace': 'normal',
            #'height': 'auto'
        #},
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in df.to_dict('records')
        ],
        tooltip_duration=None
    ),

    html.Br(),
    html.Br(),
    html.Div(id='choromap-container'),
    html.Button("Update Table from Database", id="update_table"),
    html.P(id='placeholder')

])


# -------------------------------------------------------------------------------------
# Create line chart
@app.callback(
    [Output(component_id='line-container', component_property='children'),
    Output(component_id='datatable-interactivity', component_property='data')],
    [Input(component_id='datatable-interactivity', component_property="derived_virtual_data"),
     #Input(component_id='datatable-interactivity', component_property='derived_virtual_selected_rows'),
     #Input(component_id='datatable-interactivity', component_property='derived_virtual_selected_row_ids'),
     Input(component_id='datatable-interactivity', component_property="selected_rows")
     #Input(component_id='datatable-interactivity', component_property='derived_virtual_indices'),
     #Input(component_id='datatable-interactivity', component_property='derived_virtual_row_ids'),
     #Input(component_id='datatable-interactivity', component_property='active_cell'),
     #Input(component_id='datatable-interactivity', component_property='selected_cells')
     ]
)
#def update_bar(all_rows_data, slctd_row_indices, slct_rows_names, slctd_rows,
               #order_of_rows_indices, order_of_rows_names, actv_cell, slctd_cell):
def update_bar(all_rows_data, slctd_rows):
    #print('***************************************************************************')
    #print('Data across all pages pre or post filtering: {}'.format(all_rows_data))
    #print('---------------------------------------------')
    #print("Indices of selected rows if part of table after filtering:{}".format(slctd_row_indices))
    #print("Names of selected rows if part of table after filtering: {}".format(slct_rows_names))
    #print("Indices of selected rows regardless of filtering results: {}".format(slctd_rows))
    #print('---------------------------------------------')
    #print("Indices of all rows pre or post filtering: {}".format(order_of_rows_indices))
    #print("Names of all rows pre or post filtering: {}".format(order_of_rows_names))
    #print("---------------------------------------------")
    #print("Complete data of active cell: {}".format(actv_cell))
    #print("Complete data of all selected cells: {}".format(slctd_cell))

    # Declare global variable for storing SQL plotter.db contents
    global df
    global db_name
    global path_to_emc_plotter_db

    # Declare global variable dff for storing table data (needed because we don't want to reload the data from rows on each callback + all_rows_data effected by filtering and we want to keep original table to be able to keep plotted data before filter was applied)
    global dff
    
    # Decare global variable to keep previous scltd_rows state (this is needed in order to no redraw all traces on each callback but to add new selected plot to existing figure)
    global slctd_rows_prev

    # Declare global variable for figure (needed to eliminate "referenced before asignment" error)
    global fig
    

    if slctd_rows is None:
        slctd_rows = []

    # Check what rows selection updates between previous callback and current callback selected rows list
    added, removed, common = diff_set(slctd_rows_prev, slctd_rows)

    # On first callback, store table data into pandas dataframe and plot empty figure with limits
    if dff.empty:
        dff = pd.DataFrame(all_rows_data)
        fig = add_traces_to_fig(dff, slctd_rows, path_to_emc_plotter_db)
    elif slctd_rows == []: # if selecter rows list is empty - plot empty figure with limits only (no need to re-load table data into dataframe)
        df = reload_data_from_db(path_to_emc_plotter_db + db_name) # refresh table data on first load or when no slected rows in column
        #dff = pd.DataFrame(all_rows_data)
        fig = add_traces_to_fig(dff, slctd_rows, path_to_emc_plotter_db)
    # If new row were selected - add it to the existing figure
    elif added:
        fig = add_trace_to_fig(dff, added, fig, path_to_emc_plotter_db)
    elif removed: # If row removed - replot figure completely (I have not found easy way to remove specific plots from graphs figure)
        fig = add_traces_to_fig(dff, slctd_rows, path_to_emc_plotter_db)
    
    # Save previous selection state
    slctd_rows_prev = slctd_rows.copy()
    
    # Return graph object with figure and updated table data
    return [dcc.Graph(id='line-chart', figure=fig)], df.to_dict('records')

# -------------------------------------------------------------------------------------

# Callback to reload rows data from database 
@app.callback(
    Output("placeholder", "children"),
    Input("update_table", "n_clicks"))
def update_table(n):
    global dff
    # Zero dff dataframe so that main callback with triger if dff is empty condition and relod rows data
    dff = pd.DataFrame()
    #print("button press")
    
    return " Success! "

if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run_server(host="0.0.0.0")