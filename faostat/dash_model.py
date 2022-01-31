# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 15:34:24 2022

@author: Felipe Yungstedt, Alcebíades Barbosa
"""

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
decades = np.append(['Todo o período'], decades_options)

production_itens = crops['Item'].unique()
production_indicators = crops['Element'].unique()
fertilizer_itens = fert['Item'].unique()
fertilizer_indicators = fert['Element'].unique()
pesticide_itens = pest['Item'].unique()
pesticide_indicators = pest['Element'].unique()

#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__)

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

def criaMapa(decade, indicator):
    map_df = df
    map_df= map_df[(map_df["Element"] == indicator)]
    if decade != 'Todo o período':
        map_df= map_df[(map_df["Interval"] == decade)]

    map_df = map_df[["Alpha-3 code", "continent", "Area", "Value"]]
    map_df = map_df.groupby(["Alpha-3 code", "continent", "Area"]).sum().reset_index()

    fig = px.scatter_geo(map_df, locations="Alpha-3 code", color="continent",
                        hover_name="Area", size="Value",
                        projection="natural earth",
                        title="Produtos agrícolas e pecuários: " + traducao(indicator) + " no mundo em " + decade)
    return fig

def criaBarChart(df, dfType, country, decade, indicator):
    place = 'mundo'
    if country:
        df = df[(df["Area"] == country)]
        place = country

    title = '6 maiores itens por ' + dfType + ' X ' + traducao(indicator) + ' em ' + decade + ' - local: ' + place
    
    if decade != 'Todo o período':
        df= df[(df["Interval"] == decade)]

    df = df[df['Element'] == indicator]
    df = df[["Item", "Value"]]
    df = df.groupby(["Item"]).sum().reset_index()
    df = df.nlargest(6, 'Value')
    if not df.empty:
        fig = px.bar(df, x="Value", y="Item", orientation='h')
        fig.update_traces(textposition='inside')
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
        fig.update_layout(title_text=title)
        
        '''
        fig = px.pie(df, values='Value', names='Item',
            color_discrete_sequence=px.colors.sequential.Blues)
        fig.update_traces(textposition='inside')
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
        fig.update_layout(title_text=title)
        '''
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
    place = 'mundo'
    if country:
        df = df[(df["Area"] == country)]
        place = country

    if decade != 'Todo o período':
        df= df[(df["Interval"] == decade)]
        timerange = 'Year'
        
    title = 'Evolução de ' + dfType + ' X ' + traducao(indicator) + ' em ' + decade + ' - local: ' + place

    df = df[df["Element"] == indicator]
    if not df.empty:
        df_groupby = df.groupby(["Item", timerange])["Value"].sum().reset_index()
        decadas = df_groupby[timerange].unique()
        df1 = pd.DataFrame()
        for i in decadas:
            df_filtrada_top5 = df_groupby[df_groupby[timerange] == i].nlargest(6, 'Value')
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


def traducao(termo):
    dic = { 'Agricultural Use':'Uso Agrícola',
            'Export Quantity':'Quantidade de exportação',
            'Import Quantity':'Quantidade de importação',
            'Prices Paid by Farmers':'Preços pagos pelos agricultores',
            'Production':'Produção',
            'Area harvested':'Área colhida',
            'Laying':'Postura de Ovos',
            'Producing Animals/Slaughtered':'Animais de Produção/Abatidos',
            'Production':'Produção',
            'Stocks':'Estoques',
            'Yield':'Rendimentos',
            'Yield/Carcass Weight':'Rendimento/peso da carcaça'}
    
    if(dic.get(termo)):
        return(dic.get(termo))
    else:
        return(termo)
    

app.layout = html.Div(children=[
    
    
                html.Div([
    
                    html.H1(
                        children='Estatística de Produção de Alimentos',
                        style={
                            'textAlign': 'center'
                        }
                    ),
                    
                    html.H2(
                        children='Contém gráficos de produção agrícola e pecuária em todo o mundo',
                        style={
                            'textAlign': 'center'
                        }
                    ),
        
                    html.Div([
                        dcc.Graph(
                            id='mapa',
                            style={'width': '80%', 'display': 'inline-block'}
                        )
                    ], style={'width': '65%', 'display': 'inline-block'}),
                    
                    html.Div([
                        html.Div([
                            html.Label('Período:'),
                            dcc.RadioItems(
                                id='interval',
                                options=[{'label': i, 'value': i} for i in decades],
                                value='Todo o período',
                                labelStyle={'display': 'inline-block', 'marginTop': '5px'}
                            ),
                            html.P(),
                            html.Label('Indicador para Comparação entre Países no Mapa: '),
                            dcc.Dropdown(
                                id='indicators-mapa',
                                options=[{'label': traducao(i), 'value': i} for i in production_indicators],
                                value='Production'
                            )
                        ])
                    ], style={'width': '35%', 'display': 'inline-block', 'vertical-align': 'top'})
                ]),
                
                html.Div([
                    html.Div([
                    
                        html.P(),
                        html.H3("Detalhamento de Informações"),
                        html.P()
                    ], style={'width': '20%', 'display': 'inline-block', 'vertical-align': 'top'}),
                    html.Div([
                        html.Label('Assunto para Detalhamento: '),
                        dcc.Dropdown(
                            id='detalhamento',
                            options=[
                                {'label': 'Produtos', 'value': 'Prod'},
                                {'label': 'Pesticidas', 'value': 'Pest'},
                                {'label': 'Fertilizantes', 'value': 'Fert'}
                            ],
                            value='Prod'
                        )
                    ], style={'width': '27%', 'display': 'inline-block'}),
                    html.Div([
                    ], style={'width': '3%', 'display': 'inline-block'}),
                    html.Div([
                        html.P(),
                        html.Label('Indicador para Detalhamento: '),
                        dcc.Dropdown(
                            id='indicators-detalhamento',
                            options=[{'label': traducao(i), 'value': i} for i in production_indicators],
                            value='Production'
                        )
                    ], style={'width': '47%', 'display': 'inline-block'}),
                    html.Div([
                    ], style={'width': '3%', 'display': 'inline-block'})
                ]),
                
                
                html.Div([
                    
                    dcc.Graph(
                        id='Bar',
                        style={'width': '50%', 'display': 'inline-block'}
                    ),
                    dcc.Graph(
                        id='TimeSerie',
                        style={'width': '50%', 'display': 'inline-block'}
                    )
                    
                ]),
                

                html.P(
                    children='Fonte: FAO (Food and Agriculture Organization of the United Nations)',
                    style={
                        'textAlign': 'right'
                    }
                )
                
            ])
    

@app.callback(
    Output(component_id='mapa', component_property='figure'),
    [Input(component_id='interval', component_property='value'),
    Input(component_id='indicators-mapa', component_property='value')]
)
def montaMapa(decade, indicator):
    return criaMapa(decade, indicator)

@app.callback(
    Output(component_id='Bar', component_property='figure'),
    [Input(component_id='interval', component_property='value'),
    Input(component_id='mapa', component_property='clickData'),
    Input(component_id='indicators-detalhamento', component_property='value'),
    Input(component_id='detalhamento', component_property='value')]
)
def montaBar(decade, country, indicator, detalhamento):
    
    if country:
        country = country['points'][0]['hovertext']

    ds=None
    tipo=None
    
    if(detalhamento=='Prod'):
        ds = crops;
        tipo = 'Produtos'
    elif(detalhamento=='Pest'):
        ds = pest;
        tipo = 'Pesticidas'
    elif(detalhamento=='Fert'):
        ds = fert;
        tipo = 'Fertilizantes'
       
    return criaBarChart(ds, tipo, country, decade, indicator)

@app.callback(
    Output(component_id='TimeSerie', component_property='figure'),
    [Input(component_id='interval', component_property='value'),
    Input(component_id='mapa', component_property='clickData'),
    Input(component_id='indicators-detalhamento', component_property='value'),
    Input(component_id='detalhamento', component_property='value')]
)
def montaSeries(decade, country, indicator, detalhamento):
    
    if country:
        country = country['points'][0]['hovertext']
        
    ds=None
    tipo=None
    
    if(detalhamento=='Prod'):
        ds = crops;
        tipo = 'Produtos'
    elif(detalhamento=='Pest'):
        ds = pest;
        tipo = 'Pesticidas'
    elif(detalhamento=='Fert'):
        ds = fert;
        tipo = 'Fertilizantes'
       
    return criaTimeSeries(ds, tipo, country, decade, indicator)


@app.callback(
   Output(component_id='indicators-detalhamento', component_property='options'),
   [Input(component_id='detalhamento', component_property='value')]
)
def update_options_det(detalhamento):   
    if(detalhamento=='Prod'):
        return [{'label': traducao(i), 'value': i} for i in production_indicators]
    elif(detalhamento=='Pest'):
        return [{'label': traducao(i), 'value': i} for i in pesticide_indicators] 
    elif(detalhamento=='Fert'):
        return [{'label': traducao(i), 'value': i} for i in fertilizer_indicators] 


if __name__ == '__main__':
    app.run_server(debug=True)  
