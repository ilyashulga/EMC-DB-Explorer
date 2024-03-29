import os
from sqlite3 import connect
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html


def generate_graph(df, graph_title):
    """Generate graph in JSON format to be sent to JINJA and embedded inside html"""
    # Iterate over each row in Dataframe, calculate Max(Column 2, Column 3) or Max(Ver,Hor) on each row and insert into Column 1 or Max(Ver,Hor) column
    for row in range(len(df)):
        df.at[row,'Max(Ver,Hor)'] = max(df.at[row,'Hor'], df.at[row,'Ver'])
        df.at[row,'Frequency[MHz]'] = df.at[row,'Frequency[MHz]']/1000000
    
    # create xy chart using plotly library    
    fig = px.line(df, x='Frequency[MHz]', y='Max(Ver,Hor)', log_x=True, template="plotly_white", title='%s' % graph_title)

    # Convery plotly fig to JSON object
    #graphJSON = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder)

    return fig

def add_traces_to_fig(dff, slctd_rows, path_to_emc_plotter_db):
    
    
    fig = go.Figure()
    
    # Read Limits.csv content with pandas into dataframe and add to graphs figure (RE Limits)
    try:
        df_limits = pd.read_csv(os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "Limits.csv"))
    except:
        return print("Error reading Limits.csv")
    
    df_limits.columns = ['Frequency[MHz]','CISPR11_RE_CLASS_B_Group_1', 'CISPR11_RE_CLASS_B_Group_1_Important', 'CISPR11_RE_CLASS_A_Group_1_up_to_20kVA']
    graph_name = 'Limit: CISPR11 RE CLASS B Group 1'
    fig.add_trace(go.Scatter(x=df_limits["Frequency[MHz]"], y=df_limits["CISPR11_RE_CLASS_B_Group_1"], name=graph_name, mode="lines"))
    graph_name = 'Limit (important): CISPR11 RE CLASS B Group 1'
    fig.add_trace(go.Scatter(x=df_limits["Frequency[MHz]"], y=df_limits["CISPR11_RE_CLASS_B_Group_1_Important"], name=graph_name, mode="lines"))
    graph_name = 'Limit: CISPR11 RE CLASS A Group 1 <20kVA'
    fig.add_trace(go.Scatter(x=df_limits["Frequency[MHz]"], y=df_limits["CISPR11_RE_CLASS_A_Group_1_up_to_20kVA"], name=graph_name, mode="lines", visible='legendonly'))
    
    # Read Limits.csv content with pandas into dataframe and add to graphs figure (CE Limits)
    try:
        df = pd.read_csv(os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "Limits_CE.csv"))
    except:
        return apology("Error in reading Limits_CE.csv file", 400)
    
    df.columns = ['Frequency[MHz]','CISPR11_CE_CLASS_B_Group_1_AVG', 'CISPR11_CE_CLASS_A_Group_1_AVG']
    graph_name = 'Limit: AVG CISPR11 CE CLASS B Group 1'
    fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["CISPR11_CE_CLASS_B_Group_1_AVG"], name=graph_name, mode="lines", visible='legendonly'))
    graph_name = 'Limit: AVG CISPR11 CE CLASS A Group 1'
    fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["CISPR11_CE_CLASS_A_Group_1_AVG"], name=graph_name, mode="lines", visible='legendonly'))

    # Iterate over each row in selected_rows dataframe
    for index, row in dff.iterrows():
        #print(index)
        if index in slctd_rows:
            #print(index)
            # Read csv at location specified in each row (folder + filename) - begin with local
            #print(os.path.join(os.path.abspath(os.path.dirname(__file__)), dff.at[index,'folder'], dff.at[index,'filename']))
            
            #df_traces = pd.read_csv(os.path.join(os.path.abspath(os.path.dirname(__file__)), dff.at[index,'folder'], dff.at[index,'filename']), skiprows=18)
            if dff.at[index,'filename'].endswith('.csv'):
                df_traces = pd.read_csv(os.path.join(path_to_emc_plotter_db, dff.at[index,'folder'], dff.at[index,'filename']), skiprows=18)
                
                # Change column names in dataframe to more intuitive
                df_traces.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor']
                # Iterate over each file's rows and make required calculations/substitutions
                for freq in range(len(df_traces)):
                    df_traces.at[freq,'Max(Ver,Hor)'] = max(df_traces.at[freq,'Hor'], df_traces.at[freq,'Ver'])
                    df_traces.at[freq,'Frequency[MHz]'] = df_traces.at[freq,'Frequency[MHz]']/1000000
            elif dff.at[index,'filename'].endswith('.txt'):
                df_traces = pd.read_csv(os.path.join(path_to_emc_plotter_db, dff.at[index,'folder'], dff.at[index,'filename']), delim_whitespace=True, index_col=False, skiprows=26, skipfooter=15)
                df_traces.columns = ['Frequency[MHz]','Max(Ver,Hor)']
            # create xy chart using plotly library
            graph_name = 'Score: '+ str(dff.at[index,'30-1000MHz']) + ' ' + dff.at[index,'model'] + ' ' + dff.at[index,'layout'] + ' ' + ('CL' if dff.at[index, 'is_cl'] else 'OL') + ' ' + dff.at[index,'mode'] + ' ' + str(dff.at[index,'power']) + 'W ' + dff.at[index,'comment'] + ' TraceID: ' + str(dff.at[index,'id'])
            fig.add_trace(go.Scatter(x=df_traces["Frequency[MHz]"], y=df_traces["Max(Ver,Hor)"], name=graph_name, mode="lines")) 

    # Change x-axis to log scale
    fig.update_xaxes(type="log")
    fig.update_xaxes(title_text='Frequency [MHz]',
                        title_font = {"size": 20},
                        title_standoff = 0)
    fig.update_yaxes(title_text='dBuV/m',
                        title_font = {"size": 20},
                        title_standoff = 5)
    fig.update_layout(#autosize=False,
                        #hovermode='x',
                        hoverlabel_namelength=-1, # Needed to not shorten the name of the trace on hoover (together with hoverinfo='text' in fig.add_trace(go.Scatter... above)
                        hovermode="x unified",
                        minreducedwidth=250,
                        minreducedheight=500,
                        #width=1500,
                        height=700,
                        legend=dict(
                            #yanchor="top",
                            y=-0.3,
                            #xanchor="left",
                            #x=0.01,
                            orientation='h'
                            ),
                        title={
                            'text': "Radiated Emission",
                            'y':0.95,
                            'x':0.5,
                            'xanchor': 'center',
                            'yanchor': 'top'}
                        )

    return fig 

def generate_table(dataframe, max_rows):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])


def diff_set(before, after):
    b, a = set(before), set(after)
    return list(a - b), list(b - a), list(a & b)



def add_trace_to_fig(dff, added, fig, path_to_emc_plotter_db):
    
    #df_traces = pd.read_csv(os.path.join(os.path.abspath(os.path.dirname(__file__)), dff.at[added[0],'folder'], dff.at[added[0],'filename']), skiprows=18)
    if dff.at[added[0],'filename'].endswith('.csv'):
        df_traces = pd.read_csv(os.path.join(path_to_emc_plotter_db, dff.at[added[0],'folder'], dff.at[added[0],'filename']), skiprows=18)
        # Change column names in dataframe to more intuitive
        df_traces.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor']
        # Iterate over each file's rows and make required calculations/substitutions
        for freq in range(len(df_traces)):
            df_traces.at[freq,'Max(Ver,Hor)'] = max(df_traces.at[freq,'Hor'], df_traces.at[freq,'Ver'])
            df_traces.at[freq,'Frequency[MHz]'] = df_traces.at[freq,'Frequency[MHz]']/1000000
    elif dff.at[added[0],'filename'].endswith('.txt'):
        df_traces = pd.read_csv(os.path.join(path_to_emc_plotter_db, dff.at[added[0],'folder'], dff.at[added[0],'filename']), delim_whitespace=True, index_col=False, skiprows=26, skipfooter=15)
        df_traces.columns = ['Frequency[MHz]','Max(Ver,Hor)']
    # create xy chart using plotly library
    graph_name = 'Score: '+ str(dff.at[added[0],'30-1000MHz']) + ' ' + dff.at[added[0],'model'] + ' ' + dff.at[added[0],'layout'] + ' ' + ('CL' if dff.at[added[0], 'is_cl'] else 'OL') + ' ' + dff.at[added[0],'mode'] + ' ' + str(dff.at[added[0],'power']) + 'W ' + dff.at[added[0],'comment'] + ' TraceID: ' + str(dff.at[added[0],'id'])
    fig.add_trace(go.Scatter(x=df_traces["Frequency[MHz]"], y=df_traces["Max(Ver,Hor)"], name=graph_name, mode="lines"))
    return fig


def reload_data_from_db(db_location):
    # Configure standard SQLite3
    db = connect(db_location)
    #print('Connected to db:' + str(db_location))
    
    # Read plotter.db database into a dataframe
    df = pd.read_sql("SELECT users.username, sessions.lab, sessions.type, graphs.id, scores.'30-1000MHz', scores.'30-60MHz', scores.'60-100MHz', scores.'100-200MHz', scores.'200-400MHz', scores.'400-1000MHz', graphs.timestamp, graphs.session_id, sessions.name, sessions.description, graphs.model, graphs.layout, graphs.is_potted, graphs.is_cl, graphs.mode, graphs.v_in, graphs.v_out, graphs.i_in, graphs.i_load, graphs.dc, graphs.power, graphs.is_final, sessions.folder, graphs.filename, graphs.comment FROM graphs JOIN users ON sessions.user_id = users.id JOIN sessions ON graphs.session_id = sessions.id LEFT OUTER JOIN scores ON graphs.id = scores.graph_id", db)
    df = df.rename(columns={'name': 'session'})
    #print(df.tail(10))
    
    # Close connection to plotter.db 
    db.close()

    return df
