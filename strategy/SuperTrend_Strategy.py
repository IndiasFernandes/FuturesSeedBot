from backtesting import Strategy
from strategy.SuperTrend import get_supertrend
import os
import csv

class SuperTrend(Strategy):

    atr_timeperiod = 0.537
    atr_multiplier = 0.79
    atr_method = True

    def init(self):



        self.st, self.s_upt, self.st_dt = self.I(get_supertrend, self.data.df['High'], self.data.df['Low'], self.data.df['Close'], self.atr_timeperiod,
                                                            self.atr_multiplier, self.atr_method)

        self.st = self.st[1:]
        self.s_upt = self.s_upt[1:]
        self.st_dt = self.st_dt[1:]

        # Save CSV
        last_st = float(self.st[-1])
        row = [last_st]
        output_path = './export/last_st.csv'
        if os.path.isfile(output_path):
            with open(output_path, "w", newline = '') as file:
                writer = csv.writer(file)
                writer.writerow(row)

    def next(self):

        previous_price = self.data.Close[-2]
        price = self.data.Close[-1]

        # Save CSV
        last_price = float(price)
        row = [last_price]
        output_path = './export/last_price.csv'
        if os.path.isfile(output_path):
            with open(output_path, "w", newline='') as file:
                writer = csv.writer(file)
                writer.writerow(row)
        # 0 - Long | 1 - Short | 2 - Both



        if self.st[-2] > previous_price and self.st[-1] < price:
            self.position.close()
            self.buy(size=0.99)
        elif self.st[-2] < previous_price and self.st[-1] > price:
            self.position.close()
            self.sell(size=0.99)

