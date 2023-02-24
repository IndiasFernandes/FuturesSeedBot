import os

# Function that saves Klines into CSV
def save_klines(df, path, symbol):
    df.to_csv(os.path.join(path + symbol + '.csv'), mode='a', index=False)  # save the file
    # print(f"\033[38;5;76mData saved to {path + symbol + '.csv'}!\033[0;0m")