from common.folderOrganizator import check_rmv
from getData.save_klines import save_klines
import pandas as pd

# Function that converts OHCL Dataframe into Heiken Ashi Dataframe
def heikin_ashi_converter(path, symbol, start, end):

    path_read = path + '.csv'

    # Get dataframe previously saved from binance folder
    df = pd.read_csv(path_read)

    # Duplicate initial Datataframe
    df_ha = df.copy()

    for i in range(df_ha.shape[0]):
        if i > 0:
            df_ha.loc[df_ha.index[i], 'Open'] = (df['Open'][i - 1] + df['Close'][i - 1]) / 2

        df_ha.loc[df_ha.index[i], 'Close'] = (df['Open'][i] + df['Close'][i] + df['Low'][i] + df['High'][i]) / 4

    df_ha = df_ha.iloc[0:, :]

    path_check = path + '_HA.csv'

    # Check if file already existed, otherwise delete it
    check_rmv(path_check)

    # Save new file
    save_klines(df_ha, path, '_HA')

    return