import pandas as pd
import numpy as np
import datetime
import dash

# get rsi and sma from input DataFrame
# parameter: data_file = csv file of input, rsi_period = period of rsi, sma_period = period of sma,
# show_graph = (T/F) shows graph or not
# return: updated DataFrame with rsi and sma
def get_rsi(data_file, rsi_period, sma_period, show_graph=False):
    # Load data in CSV form
    data = data_file

    # calculate the simple moving average
    sma = data['Close'].rolling(window=sma_period).mean()

    # difference in hourly closing price
    data = data.set_index(pd.DatetimeIndex(data['Date'].values))
    delta = data['Close'].diff(1)
    delta

    # get price when up and price when down
    up = delta.copy()
    down = delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    # calculate the average gain and the average loss
    avg_gain = up.rolling(window=rsi_period).mean()
    avg_loss = abs(down.rolling(window=rsi_period).mean())

    # calculate rs
    rs = avg_gain / avg_loss

    # calculate rsi
    rsi = 100.0 - (100.0 / (1.0 + rs))

    new_data = pd.DataFrame()
    new_data['Close'] = data['Close']
    new_data['RSI'] = rsi
    new_data['SMA'] = list(sma)
    return new_data


# Strategy #1: multi unit, long short
# hold multiple units
# whenever RSI go from above 70 to below 70, we sell one unit,
# whenever RSI go from below 30 to above 30, we buy one unit

# RSI Buy signal = When RSI(24) > 30 => unit +1
# RSI Sell signal = When RSI(24) < 70 => unit -1

# parameter: data_file = csv file of input, rsi_period = period of rsi, sma_period = period of sma
# return: summary and chart figure element
def strat1(data_file, rsi_period=24, sma_period=200):

    df = get_rsi(data_file, rsi_period, sma_period)
    df = df.drop(['SMA'], axis=1)
    df = df.dropna()
    df['balance'] = 0
    df['unit'] = 0
    balance = 0
    unit = 0

    for i in range(len(df)):
        if((df.iloc[i-1]['RSI']<30) & (df.iloc[i]['RSI']>30)):
            balance -= df.iloc[i]['Close']
            unit +=1
    #         print(str(i)+'buy')
        if((df.iloc[i-1]['RSI']>70) & (df.iloc[i]['RSI']<70)):
            balance += df.iloc[i]['Close']
            unit -=1
        df.iloc[[i],[2]]=balance
        df.iloc[[i],[3]]= unit
    #         print(str(i)+'sell')
    df['pnl'] = df['balance']+df['unit']*df['Close']

    price_chart_figure = {
        "data": [
            {
                "x": df.index,
                "y": df["pnl"],
                "type": "lines",
            },
        ],
        "layout": {
            "title": {
                "text": "Strategy 1: Profit & Loss",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True},
            "colorway": ["#17B897"],
        },
    }

    # build summary of strategy with risk consideration
    df_summary = pd.DataFrame()
    list1 = ['Return on Investment','Standard Deviation','Max Drawdown','Max capital requirement','Avg Capital']
    max_drawdown = round(min(df['pnl']),2)
    max_cap = round(max(abs(df['balance'])),2)
    avg_cap = round(np.mean(abs(df['balance'])),2)
    roi = round((df['pnl'].iloc[-1])/avg_cap,2)
    sd = round(np.std(df['pnl']),2)
    list2 = [roi,sd,max_drawdown,max_cap,avg_cap]
    df_summary['x'] = list1
    df_summary['y'] = list2
    return df_summary, price_chart_figure

# Strategy #2: single unit, long short
# always hold one unit of product. Whenever RSI go from above 70 to below 70, we have a position of -1 unit,
# whenever RSI go from below 30 to above 30, we have a position of 1 unit

# RSI Buy signal = When RSI(24) > 30 => unit = 1
# RSI Sell signal = When RSI(24) < 70 => unit = -1

# parameter: data_file = csv file of input, rsi_period = period of rsi, sma_period = period of sma
# return: summary and chart figure element
def strat2(data_file, rsi_period=24, sma_period=200):

    df = get_rsi(data_file, rsi_period, sma_period)
    df = df.drop(['SMA'], axis=1)
    df = df.dropna()
    df['balance'] = 0
    df['unit'] = 0
    balance = 0
    unit = 0

    for i in range(len(df)):
        if unit == 0:
            if((df.iloc[i-1]['RSI']<30) & (df.iloc[i]['RSI']>30)):
                balance -= df.iloc[i]['Close']
                unit = 1
            #             print(str(i)+'buy')
            if((df.iloc[i-1]['RSI']>70) & (df.iloc[i]['RSI']<70)):
                balance += df.iloc[i]['Close']
                unit = -1
        #             print(str(i)+'sell')
        if unit == -1:
            if((df.iloc[i-1]['RSI']<30) & (df.iloc[i]['RSI']>30)):
                balance -= df.iloc[i]['Close']*2
                unit = 1
        #             print(str(i)+'buy')
        if unit == 1:
            if((df.iloc[i-1]['RSI']>70) & (df.iloc[i]['RSI']<70)):
                balance += df.iloc[i]['Close']*2
                unit = -1
        #             print(str(i)+'sell')
        df.iloc[[i],[2]]=balance
        df.iloc[[i],[3]]= unit
        df['pnl'] = df['balance']+df['unit']*df['Close']

    price_chart_figure = {
        "data": [
            {
                "x": df.index,
                "y": df["pnl"],
                "type": "lines",
            },
        ],
        "layout": {
            "title": {
                "text": "Strategy 2: Profit & Loss",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True},
            "colorway": ["#17B897"],
        },
    }

    # build summary of strategy with risk consideration
    df_summary = pd.DataFrame()
    list1 = ['Return on Investment','Standard Deviation','Max Drawdown','Max capital requirement','Avg Capital']
    max_drawdown = round(min(df['pnl']),2)
    max_cap = round(max(abs(df['balance'])),2)
    avg_cap = round(np.mean(abs(df['balance'])),2)
    roi = round((df['pnl'].iloc[-1])/avg_cap,2)
    sd = round(np.std(df['pnl']),2)
    list2 = [roi,sd,max_drawdown,max_cap,avg_cap]
    df_summary['x'] = list1
    df_summary['y'] = list2
    return df_summary, price_chart_figure


# Strategy #3: single unit, long short, different entry point compared to strategy #2
# always hold one unit of product.
# Whenever RSI go from below 70 to above 70, we have a position of -1 unit,
# whenever RSI go from above 30 to below 30, we have a position of 1 unit

# RSI Buy signal = When RSI(24) < 30 => unit = 1
# RSI Sell signal = When RSI(24) > 70 => unit = -1

# parameter: data_file = csv file of input, rsi_period = period of rsi, sma_period = period of sma
# return: summary and chart figure element
def strat3(data_file, rsi_period=24, sma_period=200):

    df = get_rsi(data_file, rsi_period, sma_period)
    df = df.drop(['SMA'], axis=1)
    df = df.dropna()
    df['balance'] = 0
    df['unit'] = 0
    balance = 0
    unit = 0

    for i in range(len(df)):
        if unit == 0:
            if ((df.iloc[i - 1]['RSI'] > 30) & (df.iloc[i]['RSI'] < 30)):
                balance -= df.iloc[i]['Close']
                unit = 1
            #             print(str(i)+'buy')
            if ((df.iloc[i - 1]['RSI'] < 70) & (df.iloc[i]['RSI'] > 70)):
                balance += df.iloc[i]['Close']
                unit = -1
        #             print(str(i)+'sell')
        if unit == -1:
            if ((df.iloc[i - 1]['RSI'] > 30) & (df.iloc[i]['RSI'] < 30)):
                balance -= df.iloc[i]['Close'] * 2
                unit = 1
        #             print(str(i)+'buy')
        if unit == 1:
            if ((df.iloc[i - 1]['RSI'] < 70) & (df.iloc[i]['RSI'] > 70)):
                balance += df.iloc[i]['Close'] * 2
                unit = -1
        #             print(str(i)+'sell')
        df.iloc[[i], [2]] = balance
        df.iloc[[i], [3]] = unit
    df['pnl'] = df['balance'] + df['unit'] * df['Close']

    price_chart_figure = {
        "data": [
            {
                "x": df.index,
                "y": df["pnl"],
                "type": "lines",
            },
        ],
        "layout": {
            "title": {
                "text": "Strategy 3: Profit & Loss",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True},
            "colorway": ["#17B897"],
        },
    }

    # build summary of strategy with risk consideration
    df_summary = pd.DataFrame()
    list1 = ['Return on Investment','Standard Deviation','Max Drawdown','Max capital requirement','Avg Capital']
    max_drawdown = round(min(df['pnl']),2)
    max_cap = round(max(abs(df['balance'])),2)
    avg_cap = round(np.mean(abs(df['balance'])),2)
    roi = round((df['pnl'].iloc[-1])/avg_cap,2)
    sd = round(np.std(df['pnl']),2)
    list2 = [roi,sd,max_drawdown,max_cap,avg_cap]
    df_summary['x'] = list1
    df_summary['y'] = list2
    return df_summary, price_chart_figure


# Strategy #4: single unit, long short, RSI and SMA
# Here are the steps to using this RSI strategy:
# Plot a 200-period simple moving average (SMA) to determine the overall price trend.
# Add the RSI indicator and change the settings to 2 periods.
# Adjust the levels for overbought and oversold to 90 and 10.

# RSI Buy signal = When price > 200 SMA & RSI(2) < 10
# RSI Sell signal = When price < 200 SMA & RSI(2) > 90

# parameter: data_file = csv file of input, rsi_period = period of rsi, sma_period = period of sma
# return: summary and chart figure element
def strat4(data_file, rsi_period=2, sma_period=200):

    df = get_rsi(data_file, rsi_period, sma_period)
    df = df.dropna()
    df['balance'] = 0
    df['unit'] = 0
    balance = 0
    unit = 0

    for i in range(len(df)):
        if unit == 0:
            if(((df.iloc[i-1]['RSI']>10) & (df.iloc[i]['RSI']<10))&(df.iloc[i]['Close']>df.iloc[i]['SMA'])):
                balance -= df.iloc[i]['Close']
                unit = 1
    #             print(str(i)+'buy')
            if(((df.iloc[i-1]['RSI']<90) & (df.iloc[i]['RSI']>90))&(df.iloc[i]['Close']<df.iloc[i]['SMA'])):
                balance += df.iloc[i]['Close']
                unit = -1
    #             print(str(i)+'sell')
        if unit == -1:
            if(((df.iloc[i-1]['RSI']>10) & (df.iloc[i]['RSI']<10))&(df.iloc[i]['Close']>df.iloc[i]['SMA'])):
                balance -= df.iloc[i]['Close']*2
                unit = 1
    #             print(str(i)+'buy')
        if unit == 1:
            if(((df.iloc[i-1]['RSI']<90) & (df.iloc[i]['RSI']>90))&(df.iloc[i]['Close']<df.iloc[i]['SMA'])):
                balance += df.iloc[i]['Close']*2
                unit = -1
    #             print(str(i)+'sell')
        df.iloc[[i],[3]]= balance
        df.iloc[[i],[4]]= unit
    df['pnl'] = df['balance']+df['unit']*df['Close']

    price_chart_figure = {
        "data": [
            {
                "x": df.index,
                "y": df["pnl"],
                "type": "lines",
            },
        ],
        "layout": {
            "title": {
                "text": "Strategy 4: Profit & Loss",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True},
            "colorway": ["#17B897"],
        },
    }

    # build summary of strategy with risk consideration
    df_summary = pd.DataFrame()
    list1 = ['Return on Investment','Standard Deviation','Max Drawdown','Max capital requirement','Avg Capital']
    max_drawdown = round(min(df['pnl']),2)
    max_cap = round(max(abs(df['balance'])),2)
    avg_cap = round(np.mean(abs(df['balance'])),2)
    roi = round((df['pnl'].iloc[-1])/avg_cap,2)
    sd = round(np.std(df['pnl']),2)
    list2 = [roi,sd,max_drawdown,max_cap,avg_cap]
    df_summary['x'] = list1
    df_summary['y'] = list2
    return df_summary, price_chart_figure


