from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import StaticPool
import os
import enum

# Create base class for declarative models
Base = declarative_base()

class InstrumentType(enum.Enum):
    """Types of financial instruments"""
    STOCK = "stock"
    ETF = "etf"
    OPTION = "option"

class OptionType(enum.Enum):
    """Types of options"""
    CALL = "call"
    PUT = "put"

class StockDB(Base):
    """Database model for stocks and ETFs"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    name = Column(String(100))
    exchange = Column(String(20))
    instrument_type = Column(SQLEnum(InstrumentType), nullable=False)
    
    # ETF specific fields
    expense_ratio = Column(Numeric(5, 4))  # For ETFs
    assets_under_management = Column(Numeric(20, 2))  # For ETFs
    
    prices = relationship("StockPriceDB", back_populates="stock", cascade="all, delete-orphan")
    options = relationship("OptionDB", back_populates="underlying", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}', type='{self.instrument_type.value}')>"

class StockPriceDB(Base):
    """Database model for stock and ETF prices"""
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Numeric(10, 2), nullable=False)
    high = Column(Numeric(10, 2), nullable=False)
    low = Column(Numeric(10, 2), nullable=False)
    close = Column(Numeric(10, 2), nullable=False)
    volume = Column(Integer, nullable=False)
    
    # ETF specific fields
    nav = Column(Numeric(10, 2))  # Net Asset Value for ETFs
    shares_outstanding = Column(Integer)  # For ETFs
    
    stock = relationship("StockDB", back_populates="prices")
    
    def __repr__(self):
        return f"<StockPrice(symbol='{self.stock.symbol}', timestamp='{self.timestamp}')>"

class OptionDB(Base):
    """Database model for options"""
    __tablename__ = 'options'
    
    id = Column(Integer, primary_key=True)
    underlying_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    option_type = Column(SQLEnum(OptionType), nullable=False)
    strike_price = Column(Numeric(10, 2), nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    contract_size = Column(Integer, default=100)
    is_weekly = Column(Boolean, default=False)
    
    underlying = relationship("StockDB", back_populates="options")
    prices = relationship("OptionPriceDB", back_populates="option", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Option({self.option_type.value} {self.underlying.symbol} @ {self.strike_price}, exp={self.expiration_date.date()})>"

class OptionPriceDB(Base):
    """Database model for option prices"""
    __tablename__ = 'option_prices'
    
    id = Column(Integer, primary_key=True)
    option_id = Column(Integer, ForeignKey('options.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    bid = Column(Numeric(10, 2))
    ask = Column(Numeric(10, 2))
    last = Column(Numeric(10, 2))
    volume = Column(Integer)
    open_interest = Column(Integer)
    implied_volatility = Column(Numeric(10, 4))
    delta = Column(Numeric(5, 4))
    gamma = Column(Numeric(5, 4))
    theta = Column(Numeric(10, 4))
    vega = Column(Numeric(10, 4))
    rho = Column(Numeric(10, 4))
    
    option = relationship("OptionDB", back_populates="prices")
    
    def __repr__(self):
        return f"<OptionPrice(option={self.option}, timestamp='{self.timestamp}')>"

class DatabaseManager:
    """Manages database connections and operations"""
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'stocks.db')
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine with SQLite
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool
        )
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()

# Global database manager instance
db_manager = DatabaseManager() 