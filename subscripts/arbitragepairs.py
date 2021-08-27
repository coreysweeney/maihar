import ccxt
import pandas as pd
import numpy as np
import concurrent.futures

temp_list = open("exchanges.txt","r")
EXCHANGES = temp_list.read().split(',')
temp_list.close()

temp_list = open("tickers.txt","r")
SYMBOLS = temp_list.read().split(',')
temp_list.close()


def arbitrage_pair_identify(buyexchange,sellexchange,symbol):
    return_list = [buyexchange,sellexchange,0]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        buy_exchange = executor.submit(getattr , ccxt, buyexchange).result()()
        sell_exchange = executor.submit(getattr, ccxt, sellexchange).result()()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:    
        buy_data = executor.submit(get_clean_values, buy_exchange, symbol).result()
        sell_data = executor.submit(get_clean_values, sell_exchange, symbol).result()
        
    if (buy_data[0][6] and sell_data[0][5]) != 'None':
        divergence = (float(sell_data[0][5]) - float(buy_data[0][6])) / float(buy_data[0][6])
        divergence_reverse = (float(buy_data[0][5]) - float(sell_data[0][6])) / float(sell_data[0][6])
    else:
        divergence = 0
        divergence_reverse = 0
    
    output = str(round(max(divergence,divergence_reverse)*100,3)) + '%'
    
    return_list[2] = output
    
    if divergence < divergence_reverse:
        return_list[0] = sellexchange
        return_list[1] = buyexchange
    
    return(return_list)

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
        
def arbitragepairs(data_file):
    result = [0,0]
    header = ['Buy Exchange', 'Sell Exchange', 'Divergence']
    df = pd.DataFrame(np.zeros((1, 3)))
    df.columns = header
    for i in range(0,len(EXCHANGES)):
        append = arbitrage_pair_identify(data_file['exchange'].iloc[0],EXCHANGES[i],data_file['Symbol'].iloc[0])
        df.loc[len(df)] = append
    result[0] = df.drop(index=0)
    return(result)
