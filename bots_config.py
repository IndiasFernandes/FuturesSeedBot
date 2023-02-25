from datetime import datetime
from connect import config
from connect.connect_binance import connect_binance

class Bot:
  def __init__(self, name, time_start, leverage, api_key, api_secret):
    self.name = name
    self.time_start = time_start
    self.leverage = leverage
    self.api_key = api_key
    self.api_secret = api_secret

  def __str__(self):
    return f"Bot: {self.name} | leverage: {self.leverage} | Start at: {self.time_start}"

  def connect_bot(self):
    client = connect_binance(self.name, self.api_key,
                             self.api_secret)  # Connect with Binance
    return client

  def get_leverage(self):
    return self.leverage

  def get_name(self):
    return self.name


# bot_contreras = Bot('Contreras', datetime(2022, 1, 1), 5, config.API_KEY_BINANCE_CONTRERAS,
#                  config.API_SECRET_BINANCE_CONTRERAS)
#
# bot_rui = Bot('Rui', datetime(2021, 1, 1), 5, config.API_KEY_BINANCE_RUI,
#                  config.API_SECRET_BINANCE_RUI)

# Create Bot Classes
bot_indias = Bot('Indias', datetime(2021, 11, 1), 3, config.API_KEY_BINANCE_INDIAS,
                 config.API_SECRET_BINANCE_INDIAS)

bot_jeremy = Bot('Jeremy', datetime(2022, 6, 1), 6, config.API_KEY_BINANCE_JEREMY,
                 config.API_SECRET_BINANCE_JEREMY)