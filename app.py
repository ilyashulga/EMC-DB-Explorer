
from sqlite3 import connect
from dash.dependencies import Input, Output
from cs50 import SQL
from dash import Dash, html, dash_table, dcc
import plotly.express as px
import pandas as pd
import os

from helpers import generate_graph, generate_table


# Configure standard SQLite3
db = connect("plotter.db")

# App layout
app = Dash(__name__, prevent_initial_callbacks=True)

# Read csv content with pandas into dataframe starting from row 18 (otherwise pandas can't read properly the data)
filename = "All_Traces.csv"


df1 = pd.read_csv(os.path.join(filename), skiprows=18)

# Change column names in dataframe to more intuitive
df1.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor']

fig = generate_graph(df1, "test")

df2 = pd.read_sql("SELECT * FROM graphs JOIN users ON sessions.user_id = users.id JOIN sessions ON graphs.session_id = sessions.id", db)

df2.to_csv('plotter_db.csv')
print(df2.head())

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    ),

    html.H4(children='US Agriculture Exports (2011)'),
    generate_table(df2, 100)
])



if __name__ == '__main__':
    app.run_server(debug=True)