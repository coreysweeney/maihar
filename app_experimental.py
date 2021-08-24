import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_table
import pandas as pd
import numpy as np
import ccxt
import os
import time
import csv
from dash.dependencies import Output, Input, State
from datetime import timedelta

## // MAIN LIBRARY
## // TOBE EXPORTED LATER

def set_directory():
    ## sets the working directory
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

def get_paths():
    EXCHANGES_FILE = 'exchanges.txt'
    TICKERS_FILE = 'tickers.txt'
    LOG_FILE = 'log.csv'

    temp_list = open(EXCHANGES_FILE,"r")
    EXCHANGES = temp_list.read().split(',')
    temp_list.close()

    temp_list = open(TICKERS_FILE,"r")
    TICKERS = temp_list.read().split(',')
    temp_list.close()
    return(EXCHANGES,TICKERS,LOG_FILE)

def get_values(exchange,symbol):
    ## as you imagine, this retrives the values for each of the tickers
    d = {'timestamp' : [0],'exchange' : [''], 'ticker' : [0],'high' : [0], 'low' : [0], 'bid' : [0], 'ask' : [0], 'bidvolume' : [0], 'askvolume': [0], 'baseVolume': [0], 'quoteVolume': [0]}
    d = pd.DataFrame(data=d)
    ticker = exchange.fetch_ticker(symbol.upper())
    d.iloc[0,0] = ticker['timestamp']
    d.iloc[0,1] = str(exchange.id)
    d.iloc[0,2] = symbol
    d.iloc[0,3] = str(ticker['high'])
    d.iloc[0,4] = str(ticker['low'])
    d.iloc[0,5] = str(ticker['bid'])
    d.iloc[0,6] = str(ticker['ask'])
    d.iloc[0,7] = str(ticker['bidVolume'])
    d.iloc[0,8] = str(ticker['askVolume'])
    d.iloc[0,9] = str(ticker['baseVolume'])
    d.iloc[0,10] = str(ticker['quoteVolume'])
    return(d)

def return_empty_frame():
    ## in case someone puts some stupid shit into the program
    ## this will return an empty frame if an exception is thrown
    d = {'timestamp' : [0],'exchange' : [''], 'ticker' : [0],'high' : [0], 'low' : [0], 'bid' : [0], 'ask' : [0], 'bidvolume' : [0], 'askvolume': [0], 'baseVolume': [0], 'quoteVolume': [0]}
    d = pd.DataFrame(data=d)
    return(d)

def get_clean_values(exchange,symbol):
        try:
            return(get_values(exchange, symbol).values.tolist()) ## get values

        ## this is all pretty self explanatory
        ## error handling
        except ccxt.DDoSProtection as e:
            print(type(e).__name__, e.args, 'DDoS Protection (ignoring)')
            return(return_empty_frame())
        except ccxt.RequestTimeout as e:
            print(type(e).__name__, e.args, 'Request Timeout (ignoring)')
            return(return_empty_frame())
        except ccxt.ExchangeNotAvailable as e:
            print(type(e).__name__, e.args, 'Exchange Not Available due to downtime otenance (ignoring)')
            return(return_empty_frame())
        except ccxt.AuthenticationError as e:
            print(type(e).__name__, e.args, 'Authentication Error (missing API keys, ignoring)')
            return(return_empty_frame())
    
def verify_inputs(inputs):
    id = inputs[0]
    symbol = inputs[1]
    exchange_found = id in ccxt.exchanges
    if not exchange_found:
        return(0)
    exchange = getattr(ccxt, id)()
    exchange.load_markets()
    ticker_found = symbol in exchange.symbols
    if not ticker_found:
        return(0)
    return(1)

def verify(EXCHANGES,TICKERS):
    x = len(TICKERS)
    y = len(EXCHANGES)
    inputs = [0,1]
    verify_matrix = np.zeros((x,y))
    for i in range(0,x):
        for j in range(0,y):
            inputs[0] = EXCHANGES[j]
            inputs[1] = TICKERS[i]
            verify_matrix[i,j] = verify_inputs(inputs)
    np.savetxt('verified.txt',verify_matrix,fmt="%s")
    return(verify_matrix)

def main(verify_flag):
    set_directory()
    temp_paths = get_paths()
    EXCHANGES = temp_paths[0]
    TICKERS = temp_paths[1]
    LOG_FILE = temp_paths[2]
    x = len(TICKERS)
    y = len(EXCHANGES)
    if verify_flag:
        verification_matrix = verify(EXCHANGES,TICKERS)
    else:
        verification_matrix = np.loadtxt('verified.txt')
    start_time = time.time()
    for i in range(0,x):
        symbol = TICKERS[i]
        towrite = np.zeros((0,11))
        for j in range(0,y):
            if verification_matrix[i,j] == 1:
                exchange = getattr(ccxt, EXCHANGES[j])()
                towrite = np.append(towrite, get_clean_values(exchange,symbol), axis=0)
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(towrite)
    print("--- %s seconds ---" % (time.time() - start_time))

##

## // HISTORICAL DATA LIBRARY
## // WILL BE EXPORTED LATER
    
def get_historical(exchange,symbol,days):
    exch = exchange
    t_frame = '1h'
    
    try:
        exchange = getattr (ccxt, exch) ()
    except AttributeError:
        print('-'*36,' ERROR ','-'*35)
        print('Exchange "{}" not found. Please check the exchange is supported.'.format(exch))
        print('-'*80)
        quit()
        
    if exchange.has["fetchOHLCV"] != True:
        print('-'*36,' ERROR ','-'*35)
        print('{} does not support fetching OHLC data. Please use another  exchange'.format(exch))
        print('-'*80)
        quit()
    
    if (not hasattr(exchange, 'timeframes')) or (t_frame not in exchange.timeframes):
        print('-'*36,' ERROR ','-'*35)
        print('The requested timeframe ({}) is not available from {}\n'.format(t_frame,exch))
        print('Available timeframes are:')
        for key in exchange.timeframes.keys():
            print('  - ' + key)
        print('-'*80)
        quit()
    
    exchange.load_markets()
    if symbol not in exchange.symbols:
        print('-'*36,' ERROR ','-'*35)
        print('The requested symbol ({}) is not available from {}\n'.format(symbol,exch))
        print('Available symbols are:')
        for key in exchange.symbols:
            print('  - ' + key)
        print('-'*80)
        quit()
    
    header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = pd.DataFrame()
    since = exchange.milliseconds () - 86400000*days # -1000 day from now
    benchmark =  exchange.milliseconds()
    while since < benchmark - 3600000:
        data = exchange.fetch_ohlcv(symbol, t_frame, since, limit= 1000)
        data_df = pd.DataFrame(data, columns=header).set_index('Timestamp')
        data_df['Symbol'] = symbol
        data_df['exchange'] = exch
        df = df.append(data_df)
        if len(data):
            since = int(data_df.index[data_df.shape[0] - 1])
        else:
            break
        
    df.index = df.index/1000 #Timestamp is 1000 times bigger than it should be in this case
    df['Date'] = pd.to_datetime(df.index,unit='s')
    df['Timestamp'] = df.index.values
    return(df)

## // END LIBRARY

data = pd.read_csv("test.csv")
data["Date"] = pd.to_datetime(data["Date"], format="%Y/%m/%d %H:%M")
data.sort_values("Date", inplace=True)

temp_list = open("scripts.txt","r")
SCRIPTS = temp_list.read().split(',')
temp_list.close()


external_stylesheets = [
    {
        "href": "https://codepen.io/chriddyp/pen/bWLwgP.css"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Cryptocurrency Dashboard"

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
                    ]
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
                            value="RSI",
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ],
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    [
                        html.Div(children="FORCE UPDATE", className="submenu-title"),
                        daq.ToggleSwitch(
                            id='switch_one',
                            value=True
                            ),
                        html.Div(id='toggle-switch-output_one')
                    ],
                    className="dropdown",
                ),
                html.Div(
                    [
                        html.Div(children="RUN SCRIPT", className="submenu-title"),
                        daq.ToggleSwitch(
                            id='switch_three',
                            value=False
                            ),
                        html.Div(id='toggle-switch-output_three')
                    ],
                    className="dropdown",
                ),
            ],
            className="submenu",
        ),
        html.Div(
            children=[
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
            ],
            className="wrapper",
        ),
        html.Div(
            children=[
                html.Div(
                    [
                        html.Button("download csv", id="btn_csv"),
                        dcc.Download(id="download-dataframe-csv"),
                    ],
                    className="dropdown",
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
        Input("date-range", "end_date"),
        State('switch_one', 'value')
    ],
)
def update_charts(exchange, Symbol, start_date, end_date, switch_one):
    if switch_one:
        days = (pd.to_datetime(end_date)-pd.to_datetime(start_date)).days
        local_data = get_historical(exchange,Symbol,days)
    else:
        local_data = data
    mask = (
        (local_data.exchange == exchange)
        & (local_data.Symbol == Symbol)
        & (local_data.Date >= start_date)
        & (local_data.Date <= end_date)
    )
    filtered_local_data = local_data.loc[mask, :]
    mindate = np.min(local_data[(local_data.exchange == exchange) & (local_data.Symbol == Symbol)].Date)
    if mindate > pd.to_datetime(start_date):
        start_date = mindate
    maxdate = np.max(local_data[(local_data.exchange == exchange) & (local_data.Symbol == Symbol)].Date)
    if maxdate > pd.to_datetime(end_date):
        end_date = maxdate
    if pd.to_datetime(end_date) < pd.to_datetime(start_date):
        start_date = end_date
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
    return dcc.send_data_frame(df.to_csv, "mydf.csv")

if __name__ == "__main__":
    app.run_server(debug=True)