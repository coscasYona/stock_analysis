import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

class BollingerBandsStrategy:
    def __init__(self, symbol: str, window: int = 20, num_std_dev: float = 2.0):
        self.symbol = symbol
        self.window = window
        self.num_std_dev = num_std_dev
        self.data = None

    def fetch_data(self):
        """Fetch historical data from Yahoo Finance"""
        self.data = yf.download(self.symbol, start='2010-01-01', end='2020-12-31')

    def run_strategy(self):
        """Run the Bollinger Bands strategy"""
        if self.data is None:
            self.fetch_data()

        # Calculate moving average and standard deviation
        self.data['MA'] = self.data['Close'].rolling(window=self.window).mean()
        self.data['STD'] = self.data['Close'].rolling(window=self.window).std()

        # Calculate Bollinger Bands
        self.data['Upper_Band'] = self.data['MA'] + (self.data['STD'] * self.num_std_dev)
        self.data['Lower_Band'] = self.data['MA'] - (self.data['STD'] * self.num_std_dev)

        # Create signals
        self.data['Signal'] = 0
        self.data['Signal'][self.data['Close'] < self.data['Lower_Band']] = 1  # Buy
        self.data['Signal'][self.data['Close'] > self.data['Upper_Band']] = -1  # Sell

    def plot_strategy(self):
        """Plot the strategy results and save as an HD image"""
        plt.figure(figsize=(14, 7))
        plt.plot(self.data['Close'], label='Close Price')
        plt.plot(self.data['MA'], label=f'{self.window}-Day MA')
        plt.plot(self.data['Upper_Band'], label='Upper Band', linestyle='--')
        plt.plot(self.data['Lower_Band'], label='Lower Band', linestyle='--')

        # Plot buy signals
        plt.plot(self.data[self.data['Signal'] == 1].index,
                 self.data['Close'][self.data['Signal'] == 1],
                 '^', markersize=10, color='g', lw=0, label='Buy Signal')

        # Plot sell signals
        plt.plot(self.data[self.data['Signal'] == -1].index,
                 self.data['Close'][self.data['Signal'] == -1],
                 'v', markersize=10, color='r', lw=0, label='Sell Signal')

        plt.title(f'{self.symbol} Bollinger Bands Strategy')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid()
        plt.savefig(f'{self.symbol}_bollinger_bands_strategy.png', dpi=300)
        plt.close()

if __name__ == "__main__":
    strategy = BollingerBandsStrategy(symbol='^GSPC')
    strategy.run_strategy()
    strategy.plot_strategy() 