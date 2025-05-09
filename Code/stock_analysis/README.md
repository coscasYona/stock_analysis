# Stock Trading System

A scalable Python-based stock trading system that provides functionality for analyzing and trading stocks using real-time data.

## Features

- Stock data retrieval using Yahoo Finance API
- Technical analysis using pandas
- Real money trading capabilities (using Alpaca API)
- Clean, object-oriented design
- Comprehensive test coverage

## Project Structure

```
stock_analysis/
├── src/
│   ├── models/
│   │   ├── stock.py      # Stock and price data models
│   │   └── trade.py      # Trading instructions and order models
│   ├── services/         # (To be implemented)
│   │   ├── data.py      # Data retrieval service
│   │   └── trading.py   # Trading execution service
│   └── strategies/      # (To be implemented)
│       └── base.py      # Base trading strategy
├── tests/
│   ├── test_stock.py
│   └── test_trade.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd stock_analysis
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the root directory with your API credentials:
```
ALPACA_API_KEY=your_alpaca_key
ALPACA_API_SECRET=your_alpaca_secret
ALPACA_API_BASE_URL=https://paper-api.alpaca.markets  # For paper trading
```

## Running Tests

To run the test suite:
```bash
pytest
```

To run tests with coverage report:
```bash
pytest --cov=src tests/
```

## Usage

(To be implemented in future updates)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 