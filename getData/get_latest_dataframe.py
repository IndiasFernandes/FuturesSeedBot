import pandas as pd
from datetime import datetime

def get_dataframe_binance(path, start, end):
    start_object = start
    end_object = end

    df = pd.read_csv(path)
    df['time'] = df['time'].astype(str)
    df['time'] = df['time'].map(lambda x: str(x)[:-3])
    df['time'] = df['time'].astype(int)
    df['time'] = df['time'].map(lambda x: datetime.fromtimestamp(int(x)))



    # Check if there are any duplicates and drop if so
    list_duplicates = df['time'].duplicated()

    if all(list_duplicates):
        count = 0
        for element in list_duplicates:
            if element == True:
                df.drop([count - 1, 0], axis=0, inplace=True)
                print('Found one Duplicated Value - Deleted')
            count += 1

    df = df.loc[(df['time'] >= start_object) & (df['time'] <= end_object)]
    df['time'] = pd.DatetimeIndex(df['time'].values)
    df.set_index("time", inplace=True)

    # df.drop(columns=['Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume',
    #                  'Taker buy quote asset volume', 'Ignore'], inplace=True)

    return df