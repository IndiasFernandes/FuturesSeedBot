import binance.enums

from api_calls.price import get_current_price

def stop_loss(symbol, sl_percentage, side, quantity, client):


    price = get_current_price(symbol, client)
    len_price = len(str(price).split(".")[1])

    if side == 'Short':
        positionSide = 'SHORT'
        price_stop = round(price + (price * sl_percentage * 0.001), len_price)
        price_exec = round(price + (price * (sl_percentage - 1) * 0.001), len_price)
    elif side == 'Long':
        positionSide = 'LONG'
        price_stop = round(price - (price * sl_percentage * 0.001), len_price)
        price_exec = round(price - (price * (sl_percentage - 1) * 0.001), len_price)
    try:
        client.futures_create_order(positionSide=positionSide,
                                    symbol=symbol,
                                    side=binance.enums.SIDE_SELL,
                                    type=binance.enums.FUTURE_ORDER_TYPE_STOP,
                                    quantity=quantity,
                                    price=price_exec,
                                    stopPrice=price_stop)
        status = f'Added Stop-Loss of {quantity} to {symbol} at price {price}'
    except:
        status = f'Impossible to implement Stop-Loss to {symbol}'

    return status, price_stop, price_exec