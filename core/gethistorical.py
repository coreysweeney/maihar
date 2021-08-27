import ccxt
import numpy as np
import pandas as pd
def get_historical(exchange,symbol,days):
    exch = exchange
    t_frame = '1h' ## pick a timeframe for data intervals
    
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
    
    exchange.load_markets() ## need to load markets to see symbols and properties of the exchangee
    
    if symbol not in exchange.symbols:
        print('-'*36,' ERROR ','-'*35)
        print('The requested symbol ({}) is not available from {}\n'.format(symbol,exch))
        print('Available symbols are:')
        for key in exchange.symbols:
            print('  - ' + key)
        print('-'*80)
        quit()
    
    header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'] ## create titles for dataframe
    df = pd.DataFrame()
    since = exchange.milliseconds () - 86400000*days # uses unix timestamp, so multiple by number of days we go back
    benchmark =  exchange.milliseconds() ## benchmark is the current time on the exchange
    while since < benchmark - 3600000: ## as long as the reported timestamp is less than current, continue
        data = exchange.fetch_ohlcv(symbol, t_frame, since, limit= 1000) ## get data
        data_df = pd.DataFrame(data, columns=header).set_index('Timestamp')
        data_df['Symbol'] = symbol
        data_df['exchange'] = exch
        df = df.append(data_df)
        if len(data):
            since = int(data_df.index[data_df.shape[0] - 1])
        else:
            break
        
    df.index = df.index/1000 # Timestamp is 1000 times bigger than it should be in this case
    df['Date'] = pd.to_datetime(df.index,unit='s')
    df['Timestamp'] = df.index.values
    return(df)
