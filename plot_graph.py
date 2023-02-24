import pandas as pd
import matplotlib.pyplot as plt

from api_calls.price import get_current_price

df = pd.read_csv(r'export/bot_wait_log_Jeremy.csv')
df.plot(x ='Time', y=['Account Balance', 'Real Account balance'])
plt.xlabel('Time')
# plt.legend(df['Account Balance', 'Real Account balance'], loc="upper left")
plt.ylabel('Value')
plt.savefig('Ploted Account')
plt.show()
