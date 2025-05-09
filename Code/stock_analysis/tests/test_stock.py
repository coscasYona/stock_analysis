import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import os
from src.models.stock import Stock, StockPrice
from src.models.database import DatabaseManager, StockDB, StockPriceDB

@pytest.fixture
def test_db():
    """Create a test database"""
    # Use an in-memory database for testing
    db_manager = DatabaseManager("sqlite:///:memory:")
    return db_manager

@pytest.fixture
def sample_stock_price():
    return StockPrice(
        timestamp=datetime(2024, 1, 1, 10, 0),
        open=Decimal('100.00'),
        high=Decimal('105.00'),
        low=Decimal('99.00'),
        close=Decimal('102.50'),
        volume=1000
    )

@pytest.fixture
def sample_stock(test_db):
    return Stock(
        symbol='AAPL',
        name='Apple Inc.',
        exchange='NASDAQ',
        load_from_db=False  # Don't load from db initially
    )

def test_stock_price_from_dict():
    data = {
        'timestamp': '2024-01-01 10:00:00',
        'open': 100.00,
        'high': 105.00,
        'low': 99.00,
        'close': 102.50,
        'volume': 1000
    }
    price = StockPrice.from_dict(data)
    
    assert price.timestamp == pd.to_datetime('2024-01-01 10:00:00')
    assert price.open == Decimal('100.00')
    assert price.high == Decimal('105.00')
    assert price.low == Decimal('99.00')
    assert price.close == Decimal('102.50')
    assert price.volume == 1000

def test_stock_initialization(sample_stock):
    assert sample_stock.symbol == 'AAPL'
    assert sample_stock.name == 'Apple Inc.'
    assert sample_stock.exchange == 'NASDAQ'
    assert len(sample_stock._price_history) == 0
    assert sample_stock._db_id is None

def test_add_price_data(sample_stock, sample_stock_price):
    sample_stock.add_price_data(sample_stock_price)
    assert len(sample_stock._price_history) == 1
    assert sample_stock._price_history[0] == sample_stock_price

def test_save_and_load_from_db(test_db, sample_stock, sample_stock_price):
    # Add some data and save to db
    sample_stock.add_price_data(sample_stock_price)
    sample_stock.save_to_db()
    
    # Create a new stock instance that loads from db
    loaded_stock = Stock(
        symbol='AAPL',
        load_from_db=True
    )
    
    # Verify data was loaded correctly
    assert loaded_stock.symbol == sample_stock.symbol
    assert loaded_stock.name == sample_stock.name
    assert loaded_stock.exchange == sample_stock.exchange
    assert len(loaded_stock._price_history) == 1
    
    loaded_price = loaded_stock._price_history[0]
    assert loaded_price.timestamp == sample_stock_price.timestamp
    assert loaded_price.open == sample_stock_price.open
    assert loaded_price.close == sample_stock_price.close

def test_fetch_data_from_yahoo(sample_stock):
    # Test fetching recent data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    
    sample_stock.fetch_data_from_yahoo(
        start_date=start_date,
        end_date=end_date,
        save_to_db=False  # Don't save to db for this test
    )
    
    # Verify we got some data
    assert len(sample_stock._price_history) > 0
    
    # Verify the data is within our date range
    for price in sample_stock._price_history:
        assert start_date <= price.timestamp <= end_date
        assert isinstance(price.open, Decimal)
        assert isinstance(price.high, Decimal)
        assert isinstance(price.low, Decimal)
        assert isinstance(price.close, Decimal)
        assert isinstance(price.volume, int)

def test_get_price_history_with_dates(sample_stock):
    prices = [
        StockPrice(
            timestamp=datetime(2024, 1, i, 10, 0),
            open=Decimal('100.00'),
            high=Decimal('105.00'),
            low=Decimal('99.00'),
            close=Decimal('102.50'),
            volume=1000
        )
        for i in range(1, 6)
    ]
    
    for price in prices:
        sample_stock.add_price_data(price)
    
    # Test with start_date
    filtered = sample_stock.get_price_history(
        start_date=datetime(2024, 1, 3)
    )
    assert len(filtered) == 3
    
    # Test with end_date
    filtered = sample_stock.get_price_history(
        end_date=datetime(2024, 1, 3)
    )
    assert len(filtered) == 3
    
    # Test with both dates
    filtered = sample_stock.get_price_history(
        start_date=datetime(2024, 1, 2),
        end_date=datetime(2024, 1, 4)
    )
    assert len(filtered) == 3

def test_get_latest_price(sample_stock, sample_stock_price):
    assert sample_stock.get_latest_price() is None
    
    sample_stock.add_price_data(sample_stock_price)
    latest = sample_stock.get_latest_price()
    assert latest == sample_stock_price
    
    newer_price = StockPrice(
        timestamp=datetime(2024, 1, 2, 10, 0),
        open=Decimal('102.50'),
        high=Decimal('106.00'),
        low=Decimal('101.00'),
        close=Decimal('105.00'),
        volume=1200
    )
    sample_stock.add_price_data(newer_price)
    latest = sample_stock.get_latest_price()
    assert latest == newer_price

def test_to_dataframe(sample_stock, sample_stock_price):
    sample_stock.add_price_data(sample_stock_price)
    df = sample_stock.to_dataframe()
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.index.name == 'timestamp'
    assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume']
    assert df.iloc[0]['close'] == float(sample_stock_price.close) 