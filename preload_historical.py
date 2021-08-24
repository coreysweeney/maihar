import os
import ccxt
import pandas as pd


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

if __name__ == '__main__':
    set_directory()
    temp_paths = get_paths()
    exchange_list = temp_paths[0]
    exch = exchange_list[0]
    symbol = temp_paths[1]

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
    if symbol[0] not in exchange.symbols:
        print('-'*36,' ERROR ','-'*35)
        print('The requested symbol ({}) is not available from {}\n'.format(symbol,exch))
        print('Available symbols are:')
        for key in exchange.symbols:
            print('  - ' + key)
        print('-'*80)
        quit()
        
    data = exchange.fetch_ohlcv(symbol[0], t_frame)
    header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = pd.DataFrame(data, columns=header).set_index('Timestamp')
    df['Symbol'] = symbol[0]
    df['exchange'] = exch
    filename = '{}.csv'.format(t_frame)
    
    for exch in exchange_list:
        print(exch)
        try:
            exchange = getattr (ccxt, exch) ()
        except AttributeError:
            print('-'*36,' ERROR ','-'*35)
            print('Exchange "{}" not found. Please check the exchange is supported.'.format(exch))
            print('-'*80)
            quit()
        if exchange.has["fetchOHLCV"] != True:
            print('-'*36,' ERROR ','-'*35)
            print('{} does not support fetching OHLC data. Please use another exchange'.format(exch))
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
        for coin in exchange.symbols:
            if coin in symbol:
                try:
                    # for most exchanges max data points is 1000, can use since argument in a loop to get more historical data
                    since = exchange.milliseconds () - 86400000*7 # -1000 day from now
                    # alternatively, fetch from a certain starting datetime
                    # since = exchange.parse8601('2018-01-01T00:00:00Z')
                    data = exchange.fetch_ohlcv(coin, t_frame, since, limit= 1000) 
                except:
                    continue
                data_df = pd.DataFrame(data, columns=header).set_index('Timestamp')
                data_df['Symbol'] = coin
                data_df['exchange'] = exch
                df = df.append(data_df)
            else:
                continue
    
    df.index = df.index/1000 #Timestamp is 1000 times bigger than it should be in this case
    df['Date'] = pd.to_datetime(df.index,unit='s')
    df.to_csv('test.csv')