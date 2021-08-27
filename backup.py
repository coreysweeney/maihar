import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_table
import pandas as pd
import numpy as np
import ccxt
from dash.dependencies import Output, Input, State
from datetime import timedelta
from dash_extensions.enrich import DashProxy, MultiplexerTransform
from core import gethistorical as gh

## DECLARE SUBSCRIPTS HERE
from subscripts import rsitrade
from subscripts import arbitragepairs

##

data = pd.read_csv("preload.csv")
data["Date"] = pd.to_datetime(data["Date"], format="%Y/%m/%d %H:%M")
data.sort_values("Date", inplace=True)

## This is pretty much a legacy way to load the timeframe and exchanges
## If you ever want to add new exchanges or tickers, you have to execute preload_historical.py
## after adding them to the text files

temp_list = open("scripts.txt","r")
SCRIPTS = temp_list.read().split(',')
temp_list.close()

## initialize second table
s = (2,2)
data_two = np.zeros(s)
data_two = pd.DataFrame(data_two)

## START SERVER
app = DashProxy(prevent_initial_callbacks=True, transforms=[MultiplexerTransform()])
app.title = "Cryptocurrency Dashboard"
server = app.server
##

auth = dash_auth.BasicAuth (
    app,
    {'admin' : 'UCLASUMMER2021'}
    )

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children="📈", className="header-emoji"),
                html.H1(
                    children="Cryptocurrency Dashboard", className="header-title"
                ),
                html.P(
                    children="Analyze the behavior of cryptocurrency pair-trade prices,"
                    " recieve real-time updated pricing and volume information,"
                    " or download relevant sections of data",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Exchange", className="menu-title"),
                        dcc.Dropdown(
                            id="exchange-filter",
                            options=[
                                {"label": exchange, "value": exchange}
                                for exchange in np.sort(data.exchange.unique())
                            ],
                            value="binance",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Symbol", className="menu-title"),
                        dcc.Dropdown(
                            id="type-filter",
                            options=[
                                {"label": Symbol, "value": Symbol}
                                for Symbol in data.Symbol.unique()
                            ],
                            value="BTC/USDT",
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Date",
                            className="menu-title"
                            ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=data.Date.min().date(),
                            max_date_allowed=data.Date.max().date(),
                            start_date=(data.Date.max().date() - timedelta(days=30)),
                            end_date=data.Date.max().date(),
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(children="Script", className="menu-title"),
                        dcc.Dropdown(
                            id="script-filter",
                            options=[
                                {"label": value, "value": value}
                                for value in SCRIPTS
                            ],
                            value="arbitragepairs.arbitragepairs",
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    [
                        html.Button("download data", id="btn_csv"),
                        dcc.Download(id="download-dataframe-csv"),
                    ],
                ),
                html.Div(
                    [
                        html.Button("run script", id="btn_csv_sript"),
                        dcc.Download(id="run-script"),
                    ],
                ),
            ],
            className="submenu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dash_table.DataTable(
                        id='table',
                        columns=[{"name": i, "id": i} for i in data.columns],
                        data=data.to_dict('records'),
                        page_size=10,
                        sort_action="native",
                        sort_mode="multi"
                        ),
                    className="card",
                    ),
                html.Div(
                    children=dcc.Graph(
                        id="price-chart", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="volume-chart", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)

    
@app.callback(
    [Output("price-chart", "figure"), Output("volume-chart", "figure"),
     Output('date-range', 'start_date'), Output('date-range', 'end_date'),
     Output('table', 'columns'), Output('table', 'data')],
    [
        Input("exchange-filter", "value"),
        Input("type-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date")
    ],
)
def update_charts(exchange, Symbol, start_date, end_date):
    days = (pd.to_datetime(end_date)-pd.to_datetime(start_date)).days ## number of days we need to go back
    local_data = gh.get_historical(exchange,Symbol,days) ## create the local dataset
    mask = (
        (local_data.exchange == exchange)
        & (local_data.Symbol == Symbol)
        & (local_data.Date >= start_date)
        & (local_data.Date <= end_date)
    )
    filtered_local_data = local_data.loc[mask, :]
    ## ensure we cannot select beyond the data's minimum or maximum date
    mindate = np.min(local_data[(local_data.exchange == exchange) & (local_data.Symbol == Symbol)].Date)
    if mindate > pd.to_datetime(start_date):
        start_date = mindate
    maxdate = np.max(local_data[(local_data.exchange == exchange) & (local_data.Symbol == Symbol)].Date)
    if maxdate > pd.to_datetime(end_date):
        end_date = maxdate
    if pd.to_datetime(end_date) < pd.to_datetime(start_date):
        start_date = end_date
        
    ## create the figures to dispaly on the dashboard
    price_chart_figure = {
        "data": [
            {
                "x": filtered_local_data["Date"],
                "y": filtered_local_data["Close"],
                "type": "lines",
            },
        ],
        "layout": {
            "title": {
                "text": "Closing Price of Pair Trade",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True},
            "colorway": ["#17B897"],
        },
    }

    volume_chart_figure = {
        "data": [
            {
                "x": filtered_local_data["Date"],
                "y": filtered_local_data["Volume"],
                "type": "bar",
            },
        ],
        "layout": {
            "title": {"text": "Hourly Volume", "x": 0.05, "xanchor": "left"},
            "xaxis": {"fixedrange": True},
            "yaxis": {"fixedrange": True},
            "colorway": ["#E12D39"],
        },
    }
    ## remove the index since timestamp is a factor in the dataset
    local_data.index.name = None
    return_columns=[{"name": i, "id": i} for i in local_data.columns]
    return_data=local_data.to_dict('records')
    return price_chart_figure, volume_chart_figure, start_date, end_date, return_columns, return_data

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    State('table', 'data'),
    prevent_initial_call=True,
)
def download_historical(n_clicks, data):
    df = pd.DataFrame(data) 
    return dcc.send_data_frame(df.to_csv, "crypto_data.csv")

@app.callback(
    Output('table', 'columns'),
    Output("table", "data"),
    Output("volume-chart", "figure"),
    Input("btn_csv_sript", "n_clicks"),
    State('table', 'data'),
    State('script-filter', 'value'),
    prevent_initial_call=True,
)
def run_script(n_clicks, input_data,scriptname):
    function_name = scriptname
    input_data = pd.DataFrame.from_dict(input_data)
    result = eval(function_name + '(input_data)')
    local_data = result[0]
    local_data.index.name = None
    return_columns=[{"name": i, "id": i} for i in local_data.columns]
    return_data=local_data.to_dict('records')
    return return_columns,return_data,result[1]

if __name__ == "__main__":
    app.run_server(debug=True)