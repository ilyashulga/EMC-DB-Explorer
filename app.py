
from sqlite3 import connect
from dash.dependencies import Input, Output
from cs50 import SQL
from dash import Dash, html, dash_table, dcc
import plotly.express as px
import pandas as pd
import os
import plotly.graph_objects as go

from helpers import generate_graph, generate_table, add_traces_to_fig


# Configure standard SQLite3
db = connect("plotter.db")

# App layout
app = Dash(__name__, prevent_initial_callbacks=True)

# Read csv content with pandas into dataframe starting from row 18 (otherwise pandas can't read properly the data)
#filename = "All_Traces.csv"

# Create an empty dataframe for storing results table data (full table)
dff = pd.DataFrame()

#df1 = pd.read_csv(os.path.join(filename), skiprows=18)

# Change column names in dataframe to more intuitive
#df1.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor']

#fig = generate_graph(df1, "test")

df2 = pd.read_sql("SELECT users.username, graphs.timestamp, sessions.name, sessions.description, graphs.model, graphs.layout, graphs.is_cl, graphs.mode, graphs.v_in, graphs.v_out, graphs.i_in, graphs.i_load, graphs.dc, graphs.power, graphs.is_final, sessions.folder, graphs.filename, graphs.comment FROM graphs JOIN users ON sessions.user_id = users.id JOIN sessions ON graphs.session_id = sessions.id", db)

#df2.to_csv('plotter_db.csv')
#print(df2.head())

dff_first_load = pd.DataFrame(df2)

# Sorting operators (https://dash.plotly.com/datatable/filtering)
app.layout = html.Div([
    dash_table.DataTable(
        id='datatable-interactivity',
        columns=[
            {"name": i, "id": i, "deletable": True, "selectable": True, "hideable": True}
            if i == "username" or i == "timestamp" or i == "name" or i == "description" or i == "folder" or i == "filename"
            else {"name": i, "id": i, "deletable": True, "selectable": True}
            for i in df2.columns
        ],
        data=df2.to_dict('records'),  # the contents of the table
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
    html.Div(id='line-container'),
    html.Div(id='choromap-container')

])


# -------------------------------------------------------------------------------------
# Create line chart
@app.callback(
    Output(component_id='line-container', component_property='children'),
    [Input(component_id='datatable-interactivity', component_property="derived_virtual_data"),
     Input(component_id='datatable-interactivity', component_property='derived_virtual_selected_rows'),
     Input(component_id='datatable-interactivity', component_property='derived_virtual_selected_row_ids'),
     Input(component_id='datatable-interactivity', component_property='selected_rows'),
     Input(component_id='datatable-interactivity', component_property='derived_virtual_indices'),
     Input(component_id='datatable-interactivity', component_property='derived_virtual_row_ids'),
     Input(component_id='datatable-interactivity', component_property='active_cell'),
     Input(component_id='datatable-interactivity', component_property='selected_cells')]
)
def update_bar(all_rows_data, slctd_row_indices, slct_rows_names, slctd_rows,
               order_of_rows_indices, order_of_rows_names, actv_cell, slctd_cell):
    print('***************************************************************************')
    print('Data across all pages pre or post filtering: {}'.format(all_rows_data))
    print('---------------------------------------------')
    print("Indices of selected rows if part of table after filtering:{}".format(slctd_row_indices))
    print("Names of selected rows if part of table after filtering: {}".format(slct_rows_names))
    print("Indices of selected rows regardless of filtering results: {}".format(slctd_rows))
    print('---------------------------------------------')
    print("Indices of all rows pre or post filtering: {}".format(order_of_rows_indices))
    print("Names of all rows pre or post filtering: {}".format(order_of_rows_names))
    print("---------------------------------------------")
    print("Complete data of active cell: {}".format(actv_cell))
    print("Complete data of all selected cells: {}".format(slctd_cell))

    global dff
    
    if slctd_rows is None:
        slctd_rows = []

    if dff.empty:
        dff = pd.DataFrame(all_rows_data)


    # Add selected rows traces to figure
    fig = add_traces_to_fig(dff, slctd_rows)

    
    return [
            dcc.Graph(id='line-chart',
                      figure=fig)
        ]


# -------------------------------------------------------------------------------------




if __name__ == '__main__':
    app.run_server(debug=True)