import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

class MovingAverageStrategy:
    def __init__(self, symbol: str, short_window: int = 40, long_window: int = 100):
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.data = None

    def fetch_data(self):
        """Fetch historical data from Yahoo Finance"""
        self.data = yf.download(self.symbol, start='2010-01-01', end='2020-12-31')

    def run_strategy(self):
        """Run the moving average crossover strategy"""
        if self.data is None:
            self.fetch_data()

        # Calculate moving averages
        self.data['Short_MA'] = self.data['Close'].rolling(window=self.short_window, min_periods=1).mean()
        self.data['Long_MA'] = self.data['Close'].rolling(window=self.long_window, min_periods=1).mean()

        # Create signals
        self.data['Signal'] = 0
        self.data['Signal'][self.short_window:] = \
            (self.data['Short_MA'][self.short_window:] > self.data['Long_MA'][self.short_window:]).astype(int)

        # Generate trading orders
        self.data['Position'] = self.data['Signal'].diff()

    def plot_strategy(self):
        """Plot the strategy results and save as an HD image"""
        plt.figure(figsize=(14, 7))
        plt.plot(self.data['Close'], label='Close Price')
        plt.plot(self.data['Short_MA'], label=f'Short {self.short_window}-Day MA')
        plt.plot(self.data['Long_MA'], label=f'Long {self.long_window}-Day MA')

        # Plot buy signals
        plt.plot(self.data[self.data['Position'] == 1].index,
                 self.data['Short_MA'][self.data['Position'] == 1],
                 '^', markersize=10, color='g', lw=0, label='Buy Signal')

        # Plot sell signals
        plt.plot(self.data[self.data['Position'] == -1].index,
                 self.data['Short_MA'][self.data['Position'] == -1],
                 'v', markersize=10, color='r', lw=0, label='Sell Signal')

        plt.title(f'{self.symbol} Moving Average Strategy')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid()
        plt.savefig(f'{self.symbol}_moving_average_strategy.png', dpi=300)
        plt.close()

if __name__ == "__main__":
    strategy = MovingAverageStrategy(symbol='^GSPC')
    strategy.run_strategy()
    strategy.plot_strategy() 