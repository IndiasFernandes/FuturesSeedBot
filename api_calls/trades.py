def get_trades_info(client):

    # Search for Open Orders
    futureInfo = client.futures_position_information()

    trades = {}

    for info in futureInfo:

        if float(info["positionAmt"]) > 0:
            symbol = info["symbol"]
            positionAmt = float(info["positionAmt"])
            side = "Long"
            trades[symbol] = [positionAmt, side]

        elif float(info["positionAmt"]) < 0:
            symbol = info["symbol"]
            positionAmt = float(info["positionAmt"])
            side = "Short"
            trades[symbol] = [positionAmt, side]

    return trades