

import pandas as pd
df = pd.read_csv(r'export/bot_price_log_Indias.csv')
list = df['Price'].tolist()
side = df['Side'][0]

first_price = list[0]
max_price = max(list)
leverage = 6
feePercentage = 0.008

if side == 'Short':
      realPercentage = ((max_price / first_price) - 1) * -1 * 100
      realPercentageLev = round((realPercentage * leverage) - feePercentage * leverage, 2)

elif side == 'Long':
      realPercentage = ((max_price / first_price) - 1) * 100
      realPercentageLev = round(realPercentage * leverage - feePercentage * leverage, 2)



# RP 2 SL 1
# RP 4 SL 2
# RP 8 SL 4
# RP +10 SL High - 5

print(f'First: {first_price}'
      f'\nHighest: {max_price}'
      f'\nSide: {side}'
      f'\nrealPercentage: {realPercentage}'
      f'\nrealPercentageLev: {realPercentageLev}')