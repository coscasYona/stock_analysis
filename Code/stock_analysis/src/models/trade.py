from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

class OrderType(Enum):
    """Types of orders that can be placed"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    """Side of the trade"""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """Status of an order"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class TradeInstruction:
    """Represents a trading instruction before it becomes an order"""
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: str = "day"
    
    def validate(self) -> bool:
        """Validate the trade instruction"""
        if self.quantity <= 0:
            return False
            
        if self.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and self.limit_price is None:
            return False
            
        if self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and self.stop_price is None:
            return False
            
        return True

@dataclass
class Order:
    """Represents an order in the system"""
    instruction: TradeInstruction
    order_id: str
    status: OrderStatus
    created_at: datetime
    filled_at: Optional[datetime] = None
    filled_price: Optional[Decimal] = None
    filled_quantity: int = 0
    
    @property
    def is_active(self) -> bool:
        """Check if the order is still active"""
        return self.status == OrderStatus.PENDING
    
    @property
    def is_complete(self) -> bool:
        """Check if the order is complete (filled or cancelled)"""
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]
    
    def update_status(
        self,
        new_status: OrderStatus,
        filled_price: Optional[Decimal] = None,
        filled_quantity: Optional[int] = None
    ) -> None:
        """Update the order status and fill information"""
        self.status = new_status
        
        if new_status == OrderStatus.FILLED:
            self.filled_at = datetime.now()
            if filled_price is not None:
                self.filled_price = filled_price
            if filled_quantity is not None:
                self.filled_quantity = filled_quantity 