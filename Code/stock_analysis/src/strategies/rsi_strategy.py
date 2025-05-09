import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

class RSIStrategy:
    def __init__(self, symbol: str, window: int = 14, overbought: int = 70, oversold: int = 30):
        self.symbol = symbol
        self.window = window
        self.overbought = overbought
        self.oversold = oversold
        self.data = None

    def fetch_data(self):
        """Fetch historical data from Yahoo Finance"""
        self.data = yf.download(self.symbol, start='2010-01-01', end='2020-12-31')

    def run_strategy(self):
        """Run the RSI strategy"""
        if self.data is None:
            self.fetch_data()

        # Calculate RSI
        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.window).mean()
        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

        # Create signals
        self.data['Signal'] = 0
        self.data['Signal'][self.data['RSI'] < self.oversold] = 1  # Buy
        self.data['Signal'][self.data['RSI'] > self.overbought] = -1  # Sell

    def plot_strategy(self):
        """Plot the strategy results and save as an HD image"""
        plt.figure(figsize=(14, 7))
        plt.subplot(2, 1, 1)
        plt.plot(self.data['Close'], label='Close Price')
        plt.title(f'{self.symbol} RSI Strategy')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid()

        plt.subplot(2, 1, 2)
        plt.plot(self.data['RSI'], label='RSI', color='orange')
        plt.axhline(y=self.overbought, color='r', linestyle='--', label='Overbought')
        plt.axhline(y=self.oversold, color='g', linestyle='--', label='Oversold')

        # Plot buy signals
        plt.plot(self.data[self.data['Signal'] == 1].index,
                 self.data['RSI'][self.data['Signal'] == 1],
                 '^', markersize=10, color='g', lw=0, label='Buy Signal')

        # Plot sell signals
        plt.plot(self.data[self.data['Signal'] == -1].index,
                 self.data['RSI'][self.data['Signal'] == -1],
                 'v', markersize=10, color='r', lw=0, label='Sell Signal')

        plt.xlabel('Date')
        plt.ylabel('RSI')
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.savefig(f'{self.symbol}_rsi_strategy.png', dpi=300)
        plt.close()

if __name__ == "__main__":
    strategy = RSIStrategy(symbol='^GSPC')
    strategy.run_strategy()
    strategy.plot_strategy() 