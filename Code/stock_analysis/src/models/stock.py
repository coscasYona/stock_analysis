from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import pandas as pd
from decimal import Decimal
from .database import db_manager, StockDB, StockPriceDB, InstrumentType, OptionType
import yfinance as yf
from sqlalchemy import select

@dataclass
class StockPrice:
    """Represents a stock price point in time"""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    nav: Optional[Decimal] = None  # For ETFs
    shares_outstanding: Optional[int] = None  # For ETFs
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StockPrice':
        """Create a StockPrice instance from a dictionary"""
        return cls(
            timestamp=pd.to_datetime(data['timestamp']),
            open=Decimal(str(data['open'])),
            high=Decimal(str(data['high'])),
            low=Decimal(str(data['low'])),
            close=Decimal(str(data['close'])),
            volume=int(data['volume']),
            nav=Decimal(str(data['nav'])) if data.get('nav') is not None else None,
            shares_outstanding=int(data['shares_outstanding']) if data.get('shares_outstanding') is not None else None
        )
    
    @classmethod
    def from_db_model(cls, db_price: StockPriceDB) -> 'StockPrice':
        """Create a StockPrice instance from a database model"""
        return cls(
            timestamp=db_price.timestamp,
            open=db_price.open,
            high=db_price.high,
            low=db_price.low,
            close=db_price.close,
            volume=db_price.volume,
            nav=db_price.nav,
            shares_outstanding=db_price.shares_outstanding
        )
    
    def to_db_model(self, stock_id: int) -> StockPriceDB:
        """Convert to a database model"""
        return StockPriceDB(
            stock_id=stock_id,
            timestamp=self.timestamp,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            nav=self.nav,
            shares_outstanding=self.shares_outstanding
        )

class Stock:
    """Represents a stock or ETF with its basic information and price history"""
    def __init__(
        self,
        symbol: str,
        name: Optional[str] = None,
        exchange: Optional[str] = None,
        instrument_type: InstrumentType = InstrumentType.STOCK,
        expense_ratio: Optional[Decimal] = None,
        assets_under_management: Optional[Decimal] = None,
        load_from_db: bool = True
    ):
        self.symbol = symbol.upper()
        self.name = name
        self.exchange = exchange
        self.instrument_type = instrument_type
        self.expense_ratio = expense_ratio
        self.assets_under_management = assets_under_management
        self._price_history: List[StockPrice] = []
        self._db_id: Optional[int] = None
        
        if load_from_db:
            self._load_from_db()
    
    def _load_from_db(self) -> None:
        """Load stock data from database"""
        with db_manager.get_session() as session:
            # Try to find existing stock
            stmt = select(StockDB).where(StockDB.symbol == self.symbol)
            db_stock = session.execute(stmt).scalar_one_or_none()
            
            if db_stock:
                self._db_id = db_stock.id
                self.name = db_stock.name or self.name
                self.exchange = db_stock.exchange or self.exchange
                self.instrument_type = db_stock.instrument_type
                self.expense_ratio = db_stock.expense_ratio
                self.assets_under_management = db_stock.assets_under_management
                self._price_history = [
                    StockPrice(
                        timestamp=price.timestamp,
                        open=price.open,
                        high=price.high,
                        low=price.low,
                        close=price.close,
                        volume=price.volume,
                        nav=price.nav,
                        shares_outstanding=price.shares_outstanding
                    )
                    for price in db_stock.prices
                ]
    
    def save_to_db(self) -> None:
        """Save stock data to database"""
        with db_manager.get_session() as session:
            if self._db_id is None:
                # Create new stock record
                db_stock = StockDB(
                    symbol=self.symbol,
                    name=self.name,
                    exchange=self.exchange,
                    instrument_type=self.instrument_type,
                    expense_ratio=self.expense_ratio,
                    assets_under_management=self.assets_under_management
                )
                session.add(db_stock)
                session.flush()  # This will set the id
                self._db_id = db_stock.id
            else:
                # Update existing stock record
                db_stock = session.get(StockDB, self._db_id)
                db_stock.name = self.name
                db_stock.exchange = self.exchange
                db_stock.instrument_type = self.instrument_type
                db_stock.expense_ratio = self.expense_ratio
                db_stock.assets_under_management = self.assets_under_management
                
                # Clear existing prices
                session.query(StockPriceDB).filter(
                    StockPriceDB.stock_id == self._db_id
                ).delete()
            
            # Add all price history
            for price in self._price_history:
                session.add(price.to_db_model(self._db_id))
            
            session.commit()
    
    def fetch_data_from_yahoo(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        save_to_db: bool = True
    ) -> None:
        """Fetch stock data from Yahoo Finance"""
        # Default to last 30 days if no dates provided
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
            
        # Get data from Yahoo Finance
        ticker = yf.Ticker(self.symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            return
            
        # Update stock info if not set
        if not self.name or not self.exchange:
            info = ticker.info
            self.name = info.get('longName', self.name)
            self.exchange = info.get('exchange', self.exchange)
            
            # Update ETF specific information
            if self.instrument_type == InstrumentType.ETF:
                if 'expense_ratio' in info:
                    self.expense_ratio = Decimal(str(info['expense_ratio']))
                if 'total_assets' in info:
                    self.assets_under_management = Decimal(str(info['total_assets']))
        
        # Convert to StockPrice objects
        new_prices = []
        for timestamp, row in df.iterrows():
            price = StockPrice(
                timestamp=timestamp.to_pydatetime(),
                open=Decimal(str(row['Open'])),
                high=Decimal(str(row['High'])),
                low=Decimal(str(row['Low'])),
                close=Decimal(str(row['Close'])),
                volume=int(row['Volume'])
            )
            new_prices.append(price)
        
        # Update price history
        self._price_history.extend(new_prices)
        
        # Save to database if requested
        if save_to_db:
            self.save_to_db()
    
    def fetch_options_chain(
        self,
        expiration_date: Optional[datetime] = None
    ) -> List['Option']:
        """Fetch options chain from Yahoo Finance"""
        from .option import Option  # Import here to avoid circular dependency
        
        ticker = yf.Ticker(self.symbol)
        
        # Get all expiration dates if none specified
        if expiration_date is None:
            expiration_dates = ticker.options
            if not expiration_dates:
                return []
            # Use the nearest expiration date
            expiration_date = pd.to_datetime(expiration_dates[0])
        
        # Get options chain for the specified date
        options_dict = ticker.option_chain(expiration_date.strftime('%Y-%m-%d'))
        if not options_dict:
            return []
            
        options = []
        
        # Process calls
        for _, row in options_dict.calls.iterrows():
            option = Option(
                underlying=self,
                option_type=OptionType.CALL,
                strike_price=Decimal(str(row['strike'])),
                expiration_date=expiration_date,
                contract_size=100,
                is_weekly=False  # You might want to determine this from the data
            )
            
            # Add current price data
            from .option import OptionPrice
            price = OptionPrice(
                timestamp=datetime.now(),
                bid=Decimal(str(row['bid'])) if row['bid'] > 0 else None,
                ask=Decimal(str(row['ask'])) if row['ask'] > 0 else None,
                last=Decimal(str(row['lastPrice'])) if row['lastPrice'] > 0 else None,
                volume=int(row['volume']) if row['volume'] > 0 else None,
                open_interest=int(row['openInterest']) if row['openInterest'] > 0 else None,
                implied_volatility=Decimal(str(row['impliedVolatility'])) if row['impliedVolatility'] > 0 else None,
                delta=None,  # These Greeks might be available in some data sources
                gamma=None,
                theta=None,
                vega=None,
                rho=None
            )
            option.add_price_data(price)
            options.append(option)
        
        # Process puts
        for _, row in options_dict.puts.iterrows():
            option = Option(
                underlying=self,
                option_type=OptionType.PUT,
                strike_price=Decimal(str(row['strike'])),
                expiration_date=expiration_date,
                contract_size=100,
                is_weekly=False
            )
            
            # Add current price data
            from .option import OptionPrice
            price = OptionPrice(
                timestamp=datetime.now(),
                bid=Decimal(str(row['bid'])) if row['bid'] > 0 else None,
                ask=Decimal(str(row['ask'])) if row['ask'] > 0 else None,
                last=Decimal(str(row['lastPrice'])) if row['lastPrice'] > 0 else None,
                volume=int(row['volume']) if row['volume'] > 0 else None,
                open_interest=int(row['openInterest']) if row['openInterest'] > 0 else None,
                implied_volatility=Decimal(str(row['impliedVolatility'])) if row['impliedVolatility'] > 0 else None,
                delta=None,
                gamma=None,
                theta=None,
                vega=None,
                rho=None
            )
            option.add_price_data(price)
            options.append(option)
        
        return options
    
    def add_price_data(self, price_data: StockPrice) -> None:
        """Add a price data point to the stock's history"""
        self._price_history.append(price_data)
        
    def get_price_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[StockPrice]:
        """Get price history within the specified date range"""
        filtered_history = self._price_history
        
        if start_date:
            filtered_history = [
                price for price in filtered_history
                if price.timestamp >= start_date
            ]
            
        if end_date:
            filtered_history = [
                price for price in filtered_history
                if price.timestamp <= end_date
            ]
            
        return filtered_history
    
    def get_latest_price(self) -> Optional[StockPrice]:
        """Get the most recent price data"""
        if not self._price_history:
            return None
        return max(self._price_history, key=lambda x: x.timestamp)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert price history to a pandas DataFrame"""
        if not self._price_history:
            return pd.DataFrame()
            
        data = [
            {
                'timestamp': price.timestamp,
                'open': float(price.open),
                'high': float(price.high),
                'low': float(price.low),
                'close': float(price.close),
                'volume': price.volume,
                'nav': float(price.nav) if price.nav else None,
                'shares_outstanding': price.shares_outstanding
            }
            for price in self._price_history
        ]
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df 