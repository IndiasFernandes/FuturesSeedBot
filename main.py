from datetime import datetime
import pandas as pd
import os
import time

from backtesting import Backtest
import binance
import binance.enums

from bots_config import *
from connect import config

from api_calls.price import get_current_price
from common.get_csv_value import import_csv
from connect.connect_twillio import send_message
from strategy.SuperTrend_Strategy import SuperTrend
from common.heikinAshiConverter import heikin_ashi_converter
from getData.get_data_exchange import get_data
from connect.connect_binance import connect_binance

import colorama
from colorama import Fore, Back, Style

# Initialize colorama
colorama.init(autoreset=True)

# Bot Variables
from getData.get_latest_dataframe import get_dataframe_binance

bot_symbol = 'ETHUSDT'
bot_timeperiod = '2h'
cash = 10000
commission = .008

openbrowser = False

# Initiate Variables
trade_size, account_balance, side_prediction, st_value, price_value = 0, 0, 0, 0, 0
prediction_side = ''
trade_side = ''
trade_on = False
time_actual = datetime.now()
status = 'None'

# Supertrend Variables
atr_multiplier = 1
atr_method = 1

def download_data(bot_symbol, bot_timeperiod, time_actual, time_start, client):
    get_data(bot_symbol, bot_timeperiod, time_start, time_actual, client)

    path = 'export/data/' + bot_timeperiod + "/" + bot_symbol
    heikin_ashi_converter(path, bot_symbol, time_start, time_actual)

    df = get_dataframe_binance(path + '_HA.csv', time_start, time_actual)

    return df

def download_initial_data(time_start, client):
    print(Fore.BLACK + '    - Downloading Data ', end='')

    # Download the data from binance (Only for first bot)
    df = download_data(bot_symbol, bot_timeperiod, time_actual.strftime("%m/%d/%y %H:%M:%S"),
                       time_start.strftime("%m/%d/%y %H:%M:%S"), client)

    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')

    return df

def backtest(st_value, price_value, df):
    bt = Backtest(df,
                  SuperTrend,
                  cash=cash,
                  commission=commission,
                  exclusive_orders=True)

    stats = bt.run()
    # print(stats)
    bt.plot(open_browser=openbrowser)

    data = import_csv('export/last_price.csv')

    for items in data:
        for item in items:
            price_value = float(item)

    data = import_csv('export/last_st.csv')

    for items in data:
        for item in items:
            st_value = float(item)

    # Output
    thisdict = {
        "Net Profit": round(stats["Return [%]"], 3),
        "Total Closed Trades": stats["# Trades"],
        "Percent Profitable": stats["Win Rate [%]"],
        "Profit Factor": stats["Profit Factor"],
        "Max. Drawdown": stats["Max. Drawdown [%]"],
        "Avg. Trade": stats["Return [%]"] / stats["# Trades"],  # veeeeeeer
        "St Value": st_value
    }

    df_dict = pd.DataFrame(thisdict, index=[0])

    dict_path = 'export/backtest_results/' + bot_symbol + '.csv'

    if os.path.isfile(dict_path):
        df_dict.to_csv(dict_path, mode='a', index=False, header=False)  # save the file
    else:
        df_dict.to_csv(dict_path, mode='a', index=False)

    return st_value, price_value

def get_trade_info(price, client):
    # Search for Open Orders
    futureInfo = client.futures_position_information()

    trade_on = False

    for info in futureInfo:

        if float(info["positionAmt"]) > 0 and info["symbol"] == 'ETHUSDT':
            positionAmt = float(info["positionAmt"])
            entryPrice = float(info["entryPrice"])
            leverage = int(info["leverage"])
            liquidationPrice = float(info['liquidationPrice'])

            # Calculations
            tradeSize = round((positionAmt * entryPrice) / leverage, 2)
            realPercentage = (((price / entryPrice) - 1) * 100)
            realPercentageLev = round(realPercentage * leverage - commission * leverage, 2)
            profitLoss = round(tradeSize * (realPercentageLev / 100), 2)

            side = "Long"

            trade_on = True

            return trade_on, side, positionAmt, tradeSize

        elif float(info["positionAmt"]) < 0 and info["symbol"] == 'ETHUSDT':

            positionAmt = float(info["positionAmt"])
            entryPrice = float(info["entryPrice"])
            leverage = int(info["leverage"])
            liquidationPrice = float(info['liquidationPrice'])

            # Calculations
            tradeSize = round((positionAmt * -1 * entryPrice) / leverage, 2)
            realPercentage = (((price / entryPrice) - 1) * -1 * 100)
            realPercentageLev = round((realPercentage * leverage) - commission * leverage, 2)
            profitLoss = round(tradeSize * (realPercentageLev / 100), 2)

            side = "Short"

            trade_on = True

            return trade_on, side, positionAmt, tradeSize

    if trade_on == False:
        side = 'None'
        positionAmt = 0
        tradeSize = 0
        return trade_on, side, positionAmt, tradeSize

def get_account_info(client):
    accountInfo = client.futures_account()
    accountBalance = float(accountInfo['totalWalletBalance'])
    realAccountBalance = float(accountInfo["totalMarginBalance"])
    totalMaintMargin = float(accountInfo["totalMaintMargin"])
    marginRatio = (round(totalMaintMargin / realAccountBalance, 4)) * 100

    return accountBalance, realAccountBalance, marginRatio

def sell(trade_on, side, size, client):
    status = 'Selling'

    if trade_on == True and side == 'Long':
        try:
            client.futures_create_order(symbol=bot_symbol,
                                        side=binance.enums.SIDE_SELL,
                                        type=binance.enums.ORDER_TYPE_MARKET,
                                        quantity=size)

            print(Fore.RED + f'Sold {size} of {bot_symbol}' + Fore.GREEN + f' (Long) ', end='')
            status = 'Sold'

        except:
            print(f'Impossible to do Trade {bot_symbol}')
            status = 'Not Sold'
    elif trade_on == True and side == 'Short':
        try:
            client.futures_create_order(symbol=bot_symbol,
                                        side=binance.enums.SIDE_BUY,
                                        type=binance.enums.ORDER_TYPE_MARKET,
                                        quantity=-size)
            print(Fore.RED + f'Sold {size} of {bot_symbol}' + Fore.RED + f' (Short) ', end='')
            status = 'Sold'
        except:
            print(f'Impossible to do Trade {bot_symbol}')
            status = 'Not Sold'
    else:
        status = 'Not Selling'

    return status

def buy(side, size, client):
    status = 'Buying'
    if side == 'Long':

        client.futures_create_order(symbol=bot_symbol,
                                    side=binance.enums.SIDE_BUY,
                                    type=binance.enums.ORDER_TYPE_MARKET,
                                    quantity=size)
        print(Fore.GREEN + f'Bought {size} of {bot_symbol}' + Fore.GREEN + f' (Long) ', end='')

        status = 'Bought'

    elif side == 'Short':

        client.futures_create_order(symbol=bot_symbol,
                                    side=binance.enums.SIDE_SELL,
                                    type=binance.enums.ORDER_TYPE_MARKET,
                                    quantity=size)
        print(Fore.GREEN + f'Bought {size} of {bot_symbol}' + Fore.RED + f' (Short) ', end='')
        status = 'Bought'

    return status

def loop_log(filename, account_balance, real_account_balance, margin_ratio, prediction_side, trade_side, trade_on,
              trade_size, trade_size_real, coin_price, st_value):
    print(Fore.BLACK + '    - Getting Account Information ', end='')

    actual_time = datetime.now().strftime("%m/%d/%y %H:%M:%S")

    thisdict = {
        "Time": actual_time,
        "Account Balance": account_balance,
        "Real Account Balance": real_account_balance,
        "Margin Ratio": margin_ratio,
        "Prediction Side": prediction_side,
        "Trade Side": trade_side,
        "Trade On": trade_on,
        "Trade Size": trade_size,
        "Trade Dolars": trade_size_real,
        "Coin Price": coin_price,
        "St Value": st_value
    }

    df_dict = pd.DataFrame(thisdict, index=[0])

    dict_path = 'export/' + 'bot_loop_log_' + filename + '.csv'
    if os.path.isfile(dict_path):
        df_dict.to_csv(dict_path, mode='a', index=False, header=False)  # save the file
    else:
        df_dict.to_csv(dict_path, mode='a', index=False)

    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')

    print(Fore.BLACK + '    - Sending Message ', end='')
    send_message(f"*{filename}'s Loop Done*\n\n"
                 f"*Time:* {actual_time}\n"
                 f"*Account Balance:* {round(account_balance, 2)}$\n"
                 f"*Real Account Balance:* {round(real_account_balance, 2)}$\n"
                 f"*Margin Ratio:* {margin_ratio}%\n\n"
                 f"*Prediction Side:* {prediction_side}\n\n"
                 f"*Trade On:* {trade_on}\n"
                 f"*Trade Side:* {trade_side}\n"
                 f"*Trade Size:* {trade_size} ({trade_size_real}$)\n\n"
                 f"Coin is at *price {round(coin_price, 2)}* and *st is {round(st_value, 2)}*\n\n")

    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')

    return status

def trade_log(bot_name, status, side, trade_on, size, price, st):


    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    thisdict = {
        "Time": timestamp,
        "Bot": bot_name,
        "Status": status,
        "Side": side,
        "Trade On": trade_on,
        "Size": size,
        "Price": price,
        "St": st
    }

    df_dict = pd.DataFrame(thisdict, index=[0])

    dict_path = 'export/' + 'bot_trade_log_' + bot_name + '.csv'
    if os.path.isfile(dict_path):
        df_dict.to_csv(dict_path, mode='a', index=False, header=False)  # save the file
    else:
        df_dict.to_csv(dict_path, mode='a', index=False)

def price_log(bot_name, price, side):
    print(Fore.BLACK + '    - Logging PRICE ', end='')

    actual_time = datetime.now().strftime("%m/%d/%y %H:%M:%S")
    dict_path = 'export/' + 'bot_price_log_' + bot_name + '.csv'

    thisdict = {
        "Time": actual_time,
        "Price": price,
        "Side": side
    }
    df_dict = pd.DataFrame(thisdict, index=[0])
    if os.path.isfile(dict_path):
        df_dict.to_csv(dict_path, mode='a', index=False, header=False)  # save the file
    else:
        df_dict.to_csv(dict_path, mode='a', index=False)

    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')

def delete_price_log(bot_name):

    dict_path = 'export/' + 'bot_price_log_'+bot_name+'.csv'

    if os.path.isfile(dict_path):
        os.remove(dict_path)
        print(Fore.MAGENTA + f'(Log price file deleted) ', end='')
    else:
        print(Fore.MAGENTA + f"(Log price file doesn't exist) ", end='')

def wait_log(filename, client):


    actual_time = datetime.now().strftime("%m/%d/%y %H:%M:%S")

    # Get Account Information
    accountBalance, realAccountBalance, marginRatio = get_account_info(client)

    # Get Symbol Price
    price = get_current_price(bot_symbol, client)

    # Get Trade Information
    trade_on, side, size, real_size = get_trade_info(price, client)

    thisdict = {
        "Time": actual_time,
        "Account Balance": accountBalance,
        "Real Account balance": realAccountBalance,
        "Margin Ratio": marginRatio,
        "Trade Side": side,
        "Trade On": trade_on,
        "Trade Size": size,
        "Trade Dolars": real_size
    }

    df_dict = pd.DataFrame(thisdict, index=[0])

    dict_path = 'export/' + 'bot_wait_log_' + filename + '.csv'
    if os.path.isfile(dict_path):
        df_dict.to_csv(dict_path, mode='a', index=False, header=False)  # save the file
    else:
        df_dict.to_csv(dict_path, mode='a', index=False)
    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')
    return status

def stop_loss(symbol, side, price, client):
    client.futures_cancel_all_open_orders(symbol=symbol)
    print(f'Stop-Loss for {side}'
          f'Price: for {price}')

    if side == 'Long':
        client.futures_create_order(symbol=symbol,
                                    side=binance.enums.SIDE_SELL,
                                    type=binance.enums.FUTURE_ORDER_TYPE_STOP_MARKET,
                                    stopPrice=price,
                                    closePosition=True)
    elif side == 'Short':
        client.futures_create_order(symbol=symbol,
                                    side=binance.enums.SIDE_BUY,
                                    type=binance.enums.FUTURE_ORDER_TYPE_STOP_MARKET,
                                    stopPrice=price,
                                    closePosition=True)

def check_stop_loss(bot_name, client):
    dict_path = 'export/bot_price_log_' + bot_name + '.csv'

    if os.path.isfile(dict_path):
        df = pd.read_csv(dict_path)
        list = df['Price'].tolist()
        side = df['Side'][0]

        first_price = list[0]
        max_price = max(list)
        leverage = 6
        feePercentage = 0.008

        currentPrice = get_current_price(bot_symbol, client)
        len_price = len(str(currentPrice).split(".")[1])

        if side == 'Short':
            realPercentage = ((max_price / first_price) - 1) * -1 * 100
            realPercentageLev = round((realPercentage * leverage) - feePercentage * leverage, 2)
            if realPercentageLev >= 2 and realPercentageLev < 4:
                sl_price = round((((((1 + (feePercentage * leverage)) / leverage) / 100) / -1) + 1) * first_price,
                                 len_price)
                stop_loss(bot_symbol, side, sl_price, client)
                print('Stop-Loss Changed')
            elif realPercentageLev >= 4 and realPercentageLev < 7:
                sl_price = round((((((2 + (feePercentage * leverage)) / leverage) / 100) / -1) + 1) * first_price,
                                 len_price)
                stop_loss(bot_symbol, side, sl_price, client)
                print('Stop-Loss Changed')
            elif realPercentageLev >= 7 and realPercentageLev < 10:
                sl_price = round((((((4 + (feePercentage * leverage)) / leverage) / 100) / -1) + 1) * first_price,
                                 len_price)
                stop_loss(bot_symbol, side, sl_price, client)
                print('Stop-Loss Changed')
            elif realPercentageLev >= 10:
                sl_price = round(
                    (((((realPercentageLev + (
                            feePercentage * leverage)) / leverage) / 100) / -1) + 1) * first_price,
                    len_price)
                stop_loss(bot_symbol, side, sl_price, client)
                print('Stop-Loss Changed')
        elif side == 'Long':
            realPercentage = ((max_price / first_price) - 1) * 100
            realPercentageLev = round(realPercentage * leverage - feePercentage * leverage, 2)
            if realPercentageLev >= 2 and realPercentageLev < 4:
                sl_price = round(((((1 + (feePercentage * leverage)) / leverage) / 100) + 1) * first_price, len_price)
                stop_loss(bot_symbol, side, sl_price, client)
                print('Stop-Loss Changed')
            elif realPercentageLev >= 4 and realPercentageLev < 7:
                sl_price = round(((((2 + (feePercentage * leverage)) / leverage) / 100) + 1) * first_price, len_price)
                stop_loss(bot_symbol, side, sl_price, client)
                print('Stop-Loss Changed')
            elif realPercentageLev >= 7 and realPercentageLev < 10:
                sl_price = round(((((4 + (feePercentage * leverage)) / leverage) / 100) + 1) * first_price, len_price)
                stop_loss(bot_symbol, side, sl_price, client)
                print('Stop-Loss Changed')
            elif realPercentageLev >= 10:
                sl_price = round(
                    ((((realPercentageLev + (feePercentage * leverage)) / leverage) / 100) + 1) * first_price,
                    len_price)
                stop_loss(bot_symbol, side, sl_price, client)
                print('Stop-Loss Changed')

def main_script(time_start, leverage, bot_name, client):

    # Backtest according to previous calculated values for Supertrend
    print(Fore.BLACK + '    - Starting Backtest ', end='')
    st, price = backtest(st_value, price_value, df)
    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')

    # print(f'\nst: {st}'
    #       f'\nprice: {price}')

    print(Fore.BLACK + '    - Predicting Market Side ', end='')
    prediction_side = 'None'
    if price > st:
        prediction_side = 'Long'
    elif price < st:
        prediction_side = 'Short'
    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')

    # print(f'\nprediction_side: {prediction_side}')

    # Get Trade Information
    print(Fore.BLACK + '    - Getting Trade Information ', end='')
    trade_on, side, size, real_size = get_trade_info(price, client)
    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')

    # print(f'\ntrade_on: {trade_on}'
    #       f'\nside: {side}'
    #       f'\nsize: {size} coins'
    #       f'\nreal_size: {real_size}$')

    # Get Account Information
    print(Fore.BLACK + '    - Getting Account Information ', end='')
    accountBalance, realAccountBalance, marginRatio = get_account_info(client)
    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')

    # print(f'\naccountBalance: {round(accountBalance, 2)}$'
    #       f'\nrealAccountBalance: {round(realAccountBalance, 2)}$'
    #       f'\nmarginRatio: {round(marginRatio, 2)}%')

    print(Fore.BLACK + Style.BRIGHT + ' - Trading ', end='\n')
    print(Fore.BLACK + '    - Doing Required Actions ', end='')

    if trade_on:
        # Do Trade if necessary
        if prediction_side != side:

            sell(trade_on, side, size, client)
            trade_log(bot_name, 'Sold',side, trade_on, size, price, st)
            accountBalance, realAccountBalance, marginRatio = get_account_info(client)
            full_size = round(((accountBalance * leverage) / price) * 0.97, 3)
            buy(prediction_side, full_size, client)
            trade_log(bot_name, 'Bought', side, trade_on, size, price, st)
            delete_price_log(bot_name)


        elif prediction_side != side:
            print("Trade didn't happen - Same Direction as Trade Opened")
    elif not trade_on:

        accountBalance, realAccountBalance, marginRatio = get_account_info(client)
        full_size = round(((accountBalance * leverage) / price) * 0.97, 3)
        buy(prediction_side, full_size, client)
        trade_log(bot_name, 'Sold', side, trade_on, size, price, st)
        delete_price_log(bot_name)

    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')

    # Save results into csv
    print(Fore.BLACK + Style.BRIGHT + ' - Logging ', end='\n')

    loop_log(bot_name, accountBalance, realAccountBalance, marginRatio, prediction_side, side, trade_on, size,
              real_size, price, st)


if __name__ == '__main__':

    # Print Welcome Text
    print(Fore.WHITE + Back.BLACK + Style.DIM + ' Welcome to Crypto Bot ')

    while True:

        print(Fore.BLACK + Style.BRIGHT + ' - Waiting Loop', end='\n')
        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        counter_minutes = int(datetime.now().strftime("%M"))

        # while True:
        #     timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        #     minutes = int(datetime.now().strftime("%M"))
        #     time.sleep(55)
        #
        #     if minutes == 1 or minutes == 31:
        #         break
        #     elif minutes == counter_minutes:
        #         if minutes <31:
        #             minutesLeft = 30 - minutes
        #         elif minutes >= 31:
        #             minutesLeft = 60 - minutes
        #         # LOG INDIAS BOT
        #         client = bot_indias.connect_bot()
        #         print(Fore.BLACK + '    - Logging Indias ', end='')
        #         price = get_current_price(bot_symbol, client)
        #         trade_on, side, size, real_size = get_trade_info(price, client)
        #         wait_log('Indias', client)
        #         price_log('Indias', price, side)
        #         # try:
        #         #     check_stop_loss('Indias', client)
        #         # except:
        #         #     print('Could Not Activate Stop-Loss')
        #         #     delete_price_log('Indias')
        #
        #
        #
        #         # LOG JEREMY BOT
        #         client = bot_jeremy.connect_bot()
        #         print(Fore.BLACK + '    - Logging Jeremy ', end='')
        #         price = get_current_price(bot_symbol, client)
        #         trade_on, side, size, real_size = get_trade_info(price, client)
        #         wait_log('Jeremy', client)
        #         price_log('Jeremy', price, side)
        #         # try:
        #         #     check_stop_loss('Jeremy', client)
        #         # except:
        #         #     print('Could Not Activate Stop-Loss')
        #         #     delete_price_log('Jeremy')
        #
        #         # # LOG RUI BOT
        #         # client = bot_rui.connect_bot()
        #         # print(Fore.BLACK + '    - Logging Rui ', end='')
        #         # price = get_current_price(bot_symbol, client)
        #         # trade_on, side, size, real_size = get_trade_info(price, client)
        #         # wait_log('Rui', client)
        #         # price_log('Rui', price, side)
        #         # try:
        #         #     check_stop_loss('Rui', client)
        #         # except:
        #         #     print('Could Not Activate Stop-Loss')
        #         #     delete_price_log('Rui')
        #         #
        #         # # LOG CONTRERAS BOT
        #         # client = bot_contreras.connect_bot()
        #         # print(Fore.BLACK + '    - Logging Contreras ', end='')
        #         # price = get_current_price(bot_symbol, client)
        #         # trade_on, side, size, real_size = get_trade_info(price, client)
        #         # wait_log('Contreras', client)
        #         # price_log('Contreras', price, side)
        #         # try:
        #         #     check_stop_loss('Contreras', client)
        #         # except:
        #         #     print('Could Not Activate Stop-Loss')
        #         #     delete_price_log('Contreras')
        #
        #         print(
        #             Fore.CYAN + f'    - {timestamp} - {round(minutes)} Minutes Have Passed | {round(minutesLeft)} To Go',
        #             end='\n')
        #         time.sleep(15)
        #         counter_minutes +=5


        print(Fore.BLACK + Style.BRIGHT + ' - Main Loop', end='\n')
        time_start = datetime(2021, 1, 1)


        # DOWNLOAD DATA
        client = bot_indias.connect_bot()
        df = download_initial_data(time_start, client)

        # INDIAS BOT
        print(Fore.BLACK + Style.BRIGHT + ' - Running Bot - Indias', end='\n')
        client = bot_indias.connect_bot()
        main_script(time_start, bot_indias.get_leverage(), bot_indias.get_name(), client)

        # # JEREMY BOT
        # print(Fore.BLACK + Style.BRIGHT + ' - Running Bot - Jeremy', end='\n')
        # client = bot_jeremy.connect_bot()
        # main_script(time_start, bot_jeremy.get_leverage(), bot_jeremy.get_name(), client)  # Run Script

        # # CONTRERAS BOT
        # print(Fore.BLACK + Style.BRIGHT + ' - Running Bot - Contreras', end='\n')
        # client = bot_contreras.connect_bot()
        # main_script(time_start, bot_contreras.get_leverage(), bot_contreras.get_name(), client)
        #
        # # RUI BOT
        # print(Fore.BLACK + Style.BRIGHT + ' - Running Bot - Rui', end='\n')
        # client = bot_rui.connect_bot()
        # main_script(time_start, bot_rui.get_leverage(), bot_rui.get_name(), client)





