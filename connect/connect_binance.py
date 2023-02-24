from binance import Client
from colorama import Fore, Style


def connect_binance(bot_name, api_key, api_secret):
    print(Fore.BLACK + '    - Connecting to '+ bot_name+ "'s Binance ", end='')
    client = Client(api_key, api_secret)
    print(Fore.GREEN + Style.BRIGHT + u'\u2713', end='\n')
    return client