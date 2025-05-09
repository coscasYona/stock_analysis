import pytest
from datetime import datetime
from decimal import Decimal
from src.models.trade import (
    OrderType,
    OrderSide,
    OrderStatus,
    TradeInstruction,
    Order
)

@pytest.fixture
def sample_market_instruction():
    return TradeInstruction(
        symbol='AAPL',
        side=OrderSide.BUY,
        quantity=100,
        order_type=OrderType.MARKET
    )

@pytest.fixture
def sample_limit_instruction():
    return TradeInstruction(
        symbol='AAPL',
        side=OrderSide.BUY,
        quantity=100,
        order_type=OrderType.LIMIT,
        limit_price=Decimal('150.00')
    )

@pytest.fixture
def sample_stop_limit_instruction():
    return TradeInstruction(
        symbol='AAPL',
        side=OrderSide.SELL,
        quantity=100,
        order_type=OrderType.STOP_LIMIT,
        stop_price=Decimal('145.00'),
        limit_price=Decimal('144.00')
    )

def test_trade_instruction_validation(
    sample_market_instruction,
    sample_limit_instruction,
    sample_stop_limit_instruction
):
    # Test valid instructions
    assert sample_market_instruction.validate()
    assert sample_limit_instruction.validate()
    assert sample_stop_limit_instruction.validate()
    
    # Test invalid quantity
    invalid_quantity = TradeInstruction(
        symbol='AAPL',
        side=OrderSide.BUY,
        quantity=0,
        order_type=OrderType.MARKET
    )
    assert not invalid_quantity.validate()
    
    # Test missing limit price
    invalid_limit = TradeInstruction(
        symbol='AAPL',
        side=OrderSide.BUY,
        quantity=100,
        order_type=OrderType.LIMIT
    )
    assert not invalid_limit.validate()
    
    # Test missing stop price
    invalid_stop = TradeInstruction(
        symbol='AAPL',
        side=OrderSide.SELL,
        quantity=100,
        order_type=OrderType.STOP
    )
    assert not invalid_stop.validate()

@pytest.fixture
def sample_order(sample_market_instruction):
    return Order(
        instruction=sample_market_instruction,
        order_id='order123',
        status=OrderStatus.PENDING,
        created_at=datetime(2024, 1, 1, 10, 0)
    )

def test_order_initialization(sample_order):
    assert sample_order.order_id == 'order123'
    assert sample_order.status == OrderStatus.PENDING
    assert sample_order.created_at == datetime(2024, 1, 1, 10, 0)
    assert sample_order.filled_at is None
    assert sample_order.filled_price is None
    assert sample_order.filled_quantity == 0

def test_order_status_properties(sample_order):
    assert sample_order.is_active
    assert not sample_order.is_complete
    
    sample_order.status = OrderStatus.FILLED
    assert not sample_order.is_active
    assert sample_order.is_complete
    
    sample_order.status = OrderStatus.CANCELLED
    assert not sample_order.is_active
    assert sample_order.is_complete
    
    sample_order.status = OrderStatus.REJECTED
    assert not sample_order.is_active
    assert not sample_order.is_complete

def test_order_update_status(sample_order):
    # Test updating to filled status with fill information
    sample_order.update_status(
        OrderStatus.FILLED,
        filled_price=Decimal('155.00'),
        filled_quantity=100
    )
    
    assert sample_order.status == OrderStatus.FILLED
    assert sample_order.filled_price == Decimal('155.00')
    assert sample_order.filled_quantity == 100
    assert sample_order.filled_at is not None
    
    # Test updating to cancelled status
    another_order = Order(
        instruction=sample_order.instruction,
        order_id='order124',
        status=OrderStatus.PENDING,
        created_at=datetime(2024, 1, 1, 10, 0)
    )
    
    another_order.update_status(OrderStatus.CANCELLED)
    assert another_order.status == OrderStatus.CANCELLED
    assert another_order.filled_at is None
    assert another_order.filled_price is None
    assert another_order.filled_quantity == 0 