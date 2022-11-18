
from sqlite3 import connect
from dash.dependencies import Input, Output
from cs50 import SQL
from dash import Dash, html, dash_table, dcc
import plotly.express as px
import pandas as pd
import os
import plotly.graph_objects as go

from helpers import generate_graph, generate_table, add_traces_to_fig, diff_set, add_trace_to_fig


# Configure standard SQLite3
db = connect("plotter.db")
print('Connected to db')
# App layout
app = Dash(__name__, prevent_initial_callbacks=True)

# Create variables to store callback variables (declared as global in the callback function)
dff = pd.DataFrame()
slctd_rows_prev = []
fig = go.Figure()

# Read plotter.db database into a dataframe
df = pd.read_sql("SELECT users.username, graphs.timestamp, sessions.name, sessions.description, graphs.model, graphs.layout, graphs.is_cl, graphs.mode, graphs.v_in, graphs.v_out, graphs.i_in, graphs.i_load, graphs.dc, graphs.power, graphs.is_final, sessions.folder, graphs.filename, graphs.comment FROM graphs JOIN users ON sessions.user_id = users.id JOIN sessions ON graphs.session_id = sessions.id", db)

# Close connection to plotter.db (the data read only once)
db.close()

# Sorting operators (https://dash.plotly.com/datatable/filtering)
app.layout = html.Div([html.Div(id='line-container'),
    dash_table.DataTable(
        id='datatable-interactivity',
        columns=[
            {"name": i, "id": i, "deletable": True, "selectable": True, "hideable": True}
            if i == "username" or i == "timestamp" or i == "name" or i == "description" or i == "folder" or i == "filename"
            else {"name": i, "id": i, "deletable": True, "selectable": True}
            for i in df.columns
        ],
        data=df.to_dict('records'),  # the contents of the table
        editable=True,              # allow editing of data inside all cells
        filter_action="native",     # allow filtering of data by user ('native') or not ('none')
        sort_action="native",       # enables data to be sorted per-column by user or not ('none')
        sort_mode="single",         # sort across 'multi' or 'single' columns
        column_selectable="multi",  # allow users to select 'multi' or 'single' columns
        row_selectable="multi",     # allow users to select 'multi' or 'single' rows
        row_deletable=True,         # choose if user can delete a row (True) or not (False)
        selected_columns=[],        # ids of columns that user selects
        selected_rows=[],           # indices of rows that user selects
        page_action="native",       # all data is passed to the table up-front or not ('none')
        page_current=0,             # page number that user is on
        page_size=10,                # number of rows visible per page
        style_cell={                # ensure adequate header width when text is shorter than cell's text
            'minWidth': 40, 'maxWidth': 400, 'width': 95
        },
        style_data={                # overflow cells' content into multiple lines
            'whiteSpace': 'normal',
            'height': 'auto'
        }
    ),

    html.Br(),
    html.Br(),
    html.Div(id='choromap-container')

])


# -------------------------------------------------------------------------------------
# Create line chart
@app.callback(
    Output(component_id='line-container', component_property='children'),
    [Input(component_id='datatable-interactivity', component_property="derived_virtual_data"),
     #Input(component_id='datatable-interactivity', component_property='derived_virtual_selected_rows'),
     #Input(component_id='datatable-interactivity', component_property='derived_virtual_selected_row_ids'),
     Input(component_id='datatable-interactivity', component_property='selected_rows')
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



    # Declare global variable dff (needed because we don't want to reload the data from rows on each callback + all_rows_data effected by filtering and we want to keep original table to be able to keep plotted data before filter was applied)
    global dff
    
    # Decare global variable to keep previous scltd_rows state (this is needed in order to no redraw all traces on each callback but to add new selected plot to existing figure)
    global slctd_rows_prev

    # Declare global variable for figure (needed to eliminate "referenced before asignment" error)
    global fig
    
    if slctd_rows is None:
        slctd_rows = []
    
    # On first callback, store table data into pandas dataframe and plot empty figure with limits
    if dff.empty:
        dff = pd.DataFrame(all_rows_data)
        fig = add_traces_to_fig(dff, slctd_rows)
    elif slctd_rows == []: # is selecter rows list is empty - plot empty figure with limits only (no need to re-load table data into dataframe)
        fig = add_traces_to_fig(dff, slctd_rows)

    # Check what rows selection updates between previous callback and current callback selected rows list
    added, removed, common = diff_set(slctd_rows_prev, slctd_rows)
    
    # If new row were selected - add it to the existing figure
    if added:
        fig = add_trace_to_fig(dff, added, fig)
    elif removed: # If row removed - replot figure completely (I have not found easy way to remove specific plots from graphs figure)
        fig = add_traces_to_fig(dff, slctd_rows)
    
    # Save previous selection state
    slctd_rows_prev = slctd_rows.copy()
    
    
    
    
    return [
            dcc.Graph(id='line-chart',
                      figure=fig)
        ]


# -------------------------------------------------------------------------------------




if __name__ == '__main__':
    app.run_server(debug=True)