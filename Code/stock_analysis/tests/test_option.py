import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
from src.models.stock import Stock
from src.models.option import Option, OptionPrice
from src.models.database import OptionType, InstrumentType

@pytest.fixture
def sample_stock(test_db):
    stock = Stock(
        symbol='AAPL',
        name='Apple Inc.',
        exchange='NASDAQ',
        instrument_type=InstrumentType.STOCK,
        load_from_db=False
    )
    # Add a current price
    from src.models.stock import StockPrice
    stock.add_price_data(
        StockPrice(
            timestamp=datetime.now(),
            open=Decimal('175.00'),
            high=Decimal('176.00'),
            low=Decimal('174.00'),
            close=Decimal('175.50'),
            volume=1000000
        )
    )
    return stock

@pytest.fixture
def sample_option_price():
    return OptionPrice(
        timestamp=datetime.now(),
        bid=Decimal('3.50'),
        ask=Decimal('3.70'),
        last=Decimal('3.60'),
        volume=100,
        open_interest=1000,
        implied_volatility=Decimal('0.3'),
        delta=Decimal('0.5'),
        gamma=Decimal('0.05'),
        theta=Decimal('-0.1'),
        vega=Decimal('0.2'),
        rho=Decimal('0.1')
    )

@pytest.fixture
def sample_call_option(sample_stock):
    expiration = datetime.now() + timedelta(days=30)
    return Option(
        underlying=sample_stock,
        option_type=OptionType.CALL,
        strike_price=Decimal('180.00'),
        expiration_date=expiration,
        contract_size=100,
        is_weekly=False,
        load_from_db=False
    )

@pytest.fixture
def sample_put_option(sample_stock):
    expiration = datetime.now() + timedelta(days=30)
    return Option(
        underlying=sample_stock,
        option_type=OptionType.PUT,
        strike_price=Decimal('170.00'),
        expiration_date=expiration,
        contract_size=100,
        is_weekly=False,
        load_from_db=False
    )

def test_option_price_mid_price(sample_option_price):
    assert sample_option_price.mid_price == Decimal('3.60')
    
    # Test with missing bid/ask
    price = OptionPrice(
        timestamp=datetime.now(),
        bid=None,
        ask=None,
        last=Decimal('3.60'),
        volume=100,
        open_interest=1000,
        implied_volatility=None,
        delta=None,
        gamma=None,
        theta=None,
        vega=None,
        rho=None
    )
    assert price.mid_price is None

def test_option_initialization(sample_call_option):
    assert sample_call_option.option_type == OptionType.CALL
    assert sample_call_option.strike_price == Decimal('180.00')
    assert sample_call_option.contract_size == 100
    assert not sample_call_option.is_weekly
    assert len(sample_call_option._price_history) == 0

def test_option_save_and_load(test_db, sample_call_option, sample_option_price):
    # Add price data and save
    sample_call_option.add_price_data(sample_option_price)
    sample_call_option.save_to_db()
    
    # Create new option instance and load from db
    expiration = sample_call_option.expiration_date
    loaded_option = Option(
        underlying=sample_call_option.underlying,
        option_type=OptionType.CALL,
        strike_price=Decimal('180.00'),
        expiration_date=expiration,
        load_from_db=True
    )
    
    assert loaded_option.contract_size == sample_call_option.contract_size
    assert loaded_option.is_weekly == sample_call_option.is_weekly
    assert len(loaded_option._price_history) == 1
    
    loaded_price = loaded_option._price_history[0]
    assert loaded_price.bid == sample_option_price.bid
    assert loaded_price.ask == sample_option_price.ask
    assert loaded_price.implied_volatility == sample_option_price.implied_volatility

def test_calculate_break_even(sample_call_option, sample_put_option, sample_option_price):
    # Test call option break-even
    sample_call_option.add_price_data(sample_option_price)
    break_even = sample_call_option.calculate_break_even()
    assert break_even == Decimal('180.00') + Decimal('3.60')
    
    # Test put option break-even
    sample_put_option.add_price_data(sample_option_price)
    break_even = sample_put_option.calculate_break_even()
    assert break_even == Decimal('170.00') - Decimal('3.60')

def test_calculate_intrinsic_value(sample_call_option, sample_put_option):
    # Test call option intrinsic value
    assert sample_call_option.calculate_intrinsic_value(Decimal('185.00')) == Decimal('5.00')
    assert sample_call_option.calculate_intrinsic_value(Decimal('175.00')) == Decimal('0')
    
    # Test put option intrinsic value
    assert sample_put_option.calculate_intrinsic_value(Decimal('165.00')) == Decimal('5.00')
    assert sample_put_option.calculate_intrinsic_value(Decimal('175.00')) == Decimal('0')

def test_is_in_the_money(sample_call_option, sample_put_option):
    # Test call option
    assert sample_call_option.is_in_the_money(Decimal('185.00')) is True
    assert sample_call_option.is_in_the_money(Decimal('175.00')) is False
    
    # Test put option
    assert sample_put_option.is_in_the_money(Decimal('165.00')) is True
    assert sample_put_option.is_in_the_money(Decimal('175.00')) is False
    
    # Test using current stock price
    assert sample_call_option.is_in_the_money() is False  # Stock at 175.50
    assert sample_put_option.is_in_the_money() is False  # Stock at 175.50

def test_fetch_options_chain(sample_stock):
    # This is more of an integration test
    options = sample_stock.fetch_options_chain()
    
    # Basic validation of the options chain
    assert isinstance(options, list)
    if options:  # Only test if we got data
        option = options[0]
        assert isinstance(option, Option)
        assert option.underlying == sample_stock
        assert isinstance(option.strike_price, Decimal)
        assert isinstance(option.expiration_date, datetime)
        
        # Verify we got some price data
        latest_price = option.get_latest_price()
        if latest_price:
            assert isinstance(latest_price.bid, (Decimal, type(None)))
            assert isinstance(latest_price.ask, (Decimal, type(None)))
            assert isinstance(latest_price.volume, (int, type(None))) 