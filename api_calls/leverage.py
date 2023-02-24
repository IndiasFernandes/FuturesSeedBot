def change_lev(symbol, leverage, client):
    client.futures_change_leverage(symbol=symbol,
                                   leverage=leverage)
    status = 'Changing Leverage'
    try:
        client.futures_change_leverage(symbol=symbol,
                                       leverage=leverage)
        # print(f'Sold {quantity} of {symbol}')
        status = f'Leverage of {symbol} changed to {leverage}'
    except:

        status = f"Didn't change leverage of {symbol}"

    return status
