import os
import pandas as pd
from binance.enums import HistoricalKlinesType


# Function that gets Klines from Binance (Futures or Spot)
def get_klines(interval, symbols, start, end, client):

    colnames = ['time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume',
                'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore']


    kline_type = HistoricalKlinesType.FUTURES

    klines_generator = client.get_historical_klines_generator(
                    symbol=symbols,
                    interval=interval,
                    start_str=start,
                    end_str=end,
                    klines_type=kline_type
                    )  # we will get the generator first

    klines_list = list(klines_generator)  # you can either save the generator directly or convert it to data

    df = pd.DataFrame(klines_list, columns=colnames)  # save as a pandas dataframe

    df = df.drop(['Close time', 'Quote asset volume',
                'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'], axis=1)

    # print("\033[38;5;76mData Downloaded!\033[0;0m")

    return df

# Get timestamp of earliest date data is available
def get_initial_timestamp(client, symbol, timeframe):

    from datetime import datetime
    timestamp = str(client._get_earliest_valid_timestamp(symbol, timeframe))
    timestamp = int(timestamp[:-3])
    dt_object = datetime.fromtimestamp(timestamp)

    return timestamp




