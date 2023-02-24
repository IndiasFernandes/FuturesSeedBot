from common.folderOrganizator import make_dir, check_rmv
from getData.binance import get_klines
from getData.save_klines import save_klines

def get_data(bot_symbol, bot_timeperiod, time_start, time_actual, client):

    # Build Folder
    path = './export/data'

    # Create directory for timeframe if it doesn't exists
    make_dir(path + '/', bot_timeperiod)

    check_rmv(path + "/" + bot_timeperiod + "/" + bot_symbol + ".csv")

    klines = get_klines(bot_timeperiod, bot_symbol, str(time_start), str(time_actual), client)

    save_klines(klines, path + '/' + bot_timeperiod + '/', bot_symbol)

