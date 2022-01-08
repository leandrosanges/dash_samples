import json
from textwrap import dedent as d

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

from zipfile import ZipFile

zip_file = ZipFile('dados/dados.zip')
crops = pd.read_csv(zip_file.open('production_final.csv'), encoding='iso-8859-1', sep=';')
fert = pd.read_csv(zip_file.open('fertilizer_final.csv'), encoding='iso-8859-1', sep=';')
pest = pd.read_csv(zip_file.open('pesticides_final.csv'), encoding='iso-8859-1', sep=';')


# crops = pd.read_csv("dados/production_final.csv", encoding='iso-8859-1', sep=';')
crops = crops[crops['Value'].notna()]
# fert = pd.read_csv("dados/fertilizer_final.csv", encoding='iso-8859-1', sep=';')
fert = fert[fert['Value'].notna()]
# pest = pd.read_csv("dados/pesticides_final.csv", encoding='iso-8859-1', sep=';')
pest = pest[pest['Value'].notna()]

df = crops[crops['continent'].notnull()]

available_itens = df['Item'].unique()
available_indicators = df['Element'].unique()

decades_options = df['Interval'].unique()
decades_options.sort()
decades = np.append(['All Time'], decades_options)

production_itens = crops['Item'].unique()
production_indicators = crops['Element'].unique()
fertilizer_itens = fert['Item'].unique()
fertilizer_indicators = fert['Element'].unique()
pesticide_itens = pest['Item'].unique()
pesticide_indicators = pest['Element'].unique()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__)

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

def criaMapa(decade):
    map_df = df
    map_df= map_df[(map_df["Element"] == "Production")]
    if decade != 'All Time':
        map_df= map_df[(map_df["Interval"] == decade)]

    map_df = map_df[["Alpha-3 code", "continent", "Area", "Value"]]
    map_df = map_df.groupby(["Alpha-3 code", "continent", "Area"]).sum().reset_index()

    fig = px.scatter_geo(map_df, locations="Alpha-3 code", color="continent",
                        hover_name="Area", size="Value",
                        projection="natural earth",
                        title=decade + " world's production")
    return fig

def criaPieChart(df, dfType, country, decade, indicator):
    title = "world's top 6 " + dfType + ' X ' + indicator
    if country:
        df = df[(df["Area"] == country)]
        title = country + "'s top 6 " + dfType

    if decade != 'All Time':
        df= df[(df["Interval"] == decade)]
    title = decade + ' ' + title

    df = df[df['Element'] == indicator]
    df = df[["Item", "Value"]]
    df = df.groupby(["Item"]).sum().reset_index()
    df = df.nlargest(6, 'Value')
    if not df.empty:
        fig = px.pie(df, values='Value', names='Item',
            color_discrete_sequence=px.colors.sequential.Blues)
        fig.update_traces(textposition='inside')
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
        fig.update_layout(title_text=title)
    else:
        fig = go.Figure()
        fig.update_layout(
            title_text=title,
            xaxis =  { "visible": False },
            yaxis = { "visible": False },
            annotations = [
                {   
                    "text": "No data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 28
                    }
                }
            ]
        )

    return fig

def criaTimeSeries(df, dfType, country, decade, indicator):
    timerange = 'Interval'
    title = "world's top " + dfType + ' X ' + indicator
    if country:
        df = df[(df["Area"] == country)]
        title = country + "'s top " + dfType

    if decade != 'All Time':
        df= df[(df["Interval"] == decade)]
        timerange = 'Year'
    title = decade + ' ' + title
    df = df[df["Element"] == indicator]
    if not df.empty:
        df_groupby = df.groupby(["Item", timerange])["Value"].sum().reset_index()
        decadas = df_groupby[timerange].unique()
        df1 = pd.DataFrame()
        for i in decadas:
            df_filtrada_top5 = df_groupby[df_groupby[timerange] == i].nlargest(5, 'Value')
            frames = [df1, df_filtrada_top5]
            df1 = pd.concat(frames)
        top_itens = df_groupby[df_groupby["Item"].isin(df1["Item"].unique())]
        pivot = top_itens.pivot_table('Value', [timerange], 'Item')
        pivot.reset_index( drop=False, inplace=True )
        print(pivot)
        fig = px.line(pivot, x=timerange, y=pivot.columns,
                title=title)
        fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        })
        # fig.update_xaxes(
        #     dtick="M1",
        #     tickformat="%b\n%Y")
    else:
        fig = go.Figure()
        fig.update_layout(
            title_text=title,
            xaxis =  { "visible": False },
            yaxis = { "visible": False },
            annotations = [
                {   
                    "text": "No data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 28
                    }
                }
            ]
        )
    return fig

app.layout = html.Div(children=[
                html.Div([
                    dcc.RadioItems(
                        id='interval',
                        options=[{'label': i, 'value': i} for i in decades],
                        value='All Time',
                        labelStyle={'display': 'inline-block', 'marginTop': '5px'}
                    ),
                    dcc.Graph(
                        id='mapa',
                        style={'width': '80%', 'display': 'inline-block'}
                    )
                ]),

                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id='indicators-production',
                            options=[{'label': i, 'value': i} for i in production_indicators],
                            value='Production',
                            style={'width': '30%', 'display': 'inline-block'}
                        )
                    ], style={'width': '100%', 'display': 'inline-block'}),
                    dcc.Graph(
                        id='productionPie',
                        style={'width': '50%', 'display': 'inline-block'}
                    ),
                    dcc.Graph(
                        id='productionTimeSerie',
                        style={'width': '50%', 'display': 'inline-block'}
                    ),
                    html.Div([
                        dcc.Dropdown(
                            id='indicators-fertilizer',
                            options=[{'label': i, 'value': i} for i in fertilizer_indicators],
                            value='Agricultural Use',
                            style={'width': '30%', 'display': 'inline-block'}
                        )
                    ], style={'width': '100%', 'display': 'inline-block'}),
                    dcc.Graph(
                        id='fertilizerPie',
                        style={'width': '50%', 'display': 'inline-block'}
                    ),
                    dcc.Graph(
                        id='fertilizerTimeSerie',
                        style={'width': '50%', 'display': 'inline-block'}
                    ),
                    html.Div([
                        dcc.Dropdown(
                            id='indicators-pesticides',
                            options=[{'label': i, 'value': i} for i in pesticide_indicators],
                            value='Agricultural Use',
                            style={'width': '30%', 'display': 'inline-block'}
                        )
                    ], style={'width': '100%', 'display': 'inline-block'}),
                    dcc.Graph(
                        id='pesticidePie',
                        style={'width': '50%', 'display': 'inline-block'}
                    ),
                    dcc.Graph(
                        id='pesticideTimeSerie',
                        style={'width': '50%', 'display': 'inline-block'}
                    )
                ])
            ])

@app.callback(
    Output(component_id='mapa', component_property='figure'),
    [Input(component_id='interval', component_property='value')]
)
def montaMapa(decade):
    return criaMapa(decade)

@app.callback(
    Output(component_id='productionPie', component_property='figure'),
    [Input(component_id='interval', component_property='value'),
    Input(component_id='mapa', component_property='clickData'),
    Input(component_id='indicators-production', component_property='value')]
)
def montaPieCrops(decade, country, indicator):
    print(decade)
    print(country)
    if country:
        country = country['points'][0]['hovertext']
       
    return criaPieChart(crops, 'products', country, decade, indicator)

@app.callback(
    Output(component_id='fertilizerPie', component_property='figure'),
    [Input(component_id='interval', component_property='value'),
    Input(component_id='mapa', component_property='clickData'),
    Input(component_id='indicators-fertilizer', component_property='value')]
)
def montaPieFerts(decade, country, indicator):
    if country:
        country = country['points'][0]['hovertext']
       
    return criaPieChart(fert, 'fertilizers', country, decade, indicator)

@app.callback(
    Output(component_id='pesticidePie', component_property='figure'),
    [Input(component_id='interval', component_property='value'),
    Input(component_id='mapa', component_property='clickData'),
    Input(component_id='indicators-pesticides', component_property='value')]
)
def montaPiePests(decade, country, indicator):
    if country:
        country = country['points'][0]['hovertext']
       
    return criaPieChart(pest, 'pesticides', country, decade, indicator)


@app.callback(
    Output(component_id='productionTimeSerie', component_property='figure'),
    [Input(component_id='interval', component_property='value'),
    Input(component_id='mapa', component_property='clickData'),
    Input(component_id='indicators-production', component_property='value')]
)
def montaSeriesProduction(decade, country, indicator):
    if country:
        country = country['points'][0]['hovertext']
       
    return criaTimeSeries(crops, 'products', country, decade, indicator)

@app.callback(
    Output(component_id='fertilizerTimeSerie', component_property='figure'),
    [Input(component_id='interval', component_property='value'),
    Input(component_id='mapa', component_property='clickData'),
    Input(component_id='indicators-fertilizer', component_property='value')]
)
def montaSeriesFertilizer(decade, country, indicator):
    if country:
        country = country['points'][0]['hovertext']
       
    return criaTimeSeries(fert, 'fertilizers', country, decade, indicator)

@app.callback(
    Output(component_id='pesticideTimeSerie', component_property='figure'),
    [Input(component_id='interval', component_property='value'),
    Input(component_id='mapa', component_property='clickData'),
    Input(component_id='indicators-pesticides', component_property='value')]
)
def montaSeriesPesticides(decade, country, indicator):
    if country:
        country = country['points'][0]['hovertext']
       
    return criaTimeSeries(pest, 'pesticides', country, decade, indicator)

if __name__ == '__main__':
    app.run_server(debug=True)
