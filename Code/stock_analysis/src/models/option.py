from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict
import pandas as pd
from .database import db_manager, OptionDB, OptionPriceDB, OptionType
from .stock import Stock

@dataclass
class OptionPrice:
    """Represents an option price point in time"""
    timestamp: datetime
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    last: Optional[Decimal]
    volume: Optional[int]
    open_interest: Optional[int]
    implied_volatility: Optional[Decimal]
    delta: Optional[Decimal]
    gamma: Optional[Decimal]
    theta: Optional[Decimal]
    vega: Optional[Decimal]
    rho: Optional[Decimal]
    
    @property
    def mid_price(self) -> Optional[Decimal]:
        """Calculate the mid price between bid and ask"""
        if self.bid is None or self.ask is None:
            return None
        return (self.bid + self.ask) / Decimal('2')
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OptionPrice':
        """Create an OptionPrice instance from a dictionary"""
        return cls(
            timestamp=pd.to_datetime(data['timestamp']),
            bid=Decimal(str(data['bid'])) if data.get('bid') is not None else None,
            ask=Decimal(str(data['ask'])) if data.get('ask') is not None else None,
            last=Decimal(str(data['last'])) if data.get('last') is not None else None,
            volume=int(data['volume']) if data.get('volume') is not None else None,
            open_interest=int(data['open_interest']) if data.get('open_interest') is not None else None,
            implied_volatility=Decimal(str(data['implied_volatility'])) if data.get('implied_volatility') is not None else None,
            delta=Decimal(str(data['delta'])) if data.get('delta') is not None else None,
            gamma=Decimal(str(data['gamma'])) if data.get('gamma') is not None else None,
            theta=Decimal(str(data['theta'])) if data.get('theta') is not None else None,
            vega=Decimal(str(data['vega'])) if data.get('vega') is not None else None,
            rho=Decimal(str(data['rho'])) if data.get('rho') is not None else None
        )
    
    def to_db_model(self, option_id: int) -> OptionPriceDB:
        """Convert to a database model"""
        return OptionPriceDB(
            option_id=option_id,
            timestamp=self.timestamp,
            bid=self.bid,
            ask=self.ask,
            last=self.last,
            volume=self.volume,
            open_interest=self.open_interest,
            implied_volatility=self.implied_volatility,
            delta=self.delta,
            gamma=self.gamma,
            theta=self.theta,
            vega=self.vega,
            rho=self.rho
        )

class Option:
    """Represents an option contract"""
    def __init__(
        self,
        underlying: Stock,
        option_type: OptionType,
        strike_price: Decimal,
        expiration_date: datetime,
        contract_size: int = 100,
        is_weekly: bool = False,
        load_from_db: bool = True
    ):
        self.underlying = underlying
        self.option_type = option_type
        self.strike_price = strike_price
        self.expiration_date = expiration_date
        self.contract_size = contract_size
        self.is_weekly = is_weekly
        self._price_history: List[OptionPrice] = []
        self._db_id: Optional[int] = None
        
        if load_from_db:
            self._load_from_db()
    
    def _load_from_db(self) -> None:
        """Load option data from database"""
        with db_manager.get_session() as session:
            stmt = (
                session.query(OptionDB)
                .filter(
                    OptionDB.underlying_id == self.underlying._db_id,
                    OptionDB.option_type == self.option_type,
                    OptionDB.strike_price == self.strike_price,
                    OptionDB.expiration_date == self.expiration_date
                )
            )
            db_option = session.execute(stmt).scalar_one_or_none()
            
            if db_option:
                self._db_id = db_option.id
                self.contract_size = db_option.contract_size
                self.is_weekly = db_option.is_weekly
                self._price_history = [
                    OptionPrice(
                        timestamp=price.timestamp,
                        bid=price.bid,
                        ask=price.ask,
                        last=price.last,
                        volume=price.volume,
                        open_interest=price.open_interest,
                        implied_volatility=price.implied_volatility,
                        delta=price.delta,
                        gamma=price.gamma,
                        theta=price.theta,
                        vega=price.vega,
                        rho=price.rho
                    )
                    for price in db_option.prices
                ]
    
    def save_to_db(self) -> None:
        """Save option data to database"""
        with db_manager.get_session() as session:
            if self._db_id is None:
                # Create new option record
                db_option = OptionDB(
                    underlying_id=self.underlying._db_id,
                    option_type=self.option_type,
                    strike_price=self.strike_price,
                    expiration_date=self.expiration_date,
                    contract_size=self.contract_size,
                    is_weekly=self.is_weekly
                )
                session.add(db_option)
                session.flush()  # This will set the id
                self._db_id = db_option.id
            else:
                # Update existing option record
                db_option = session.get(OptionDB, self._db_id)
                db_option.contract_size = self.contract_size
                db_option.is_weekly = self.is_weekly
                
                # Clear existing prices
                session.query(OptionPriceDB).filter(
                    OptionPriceDB.option_id == self._db_id
                ).delete()
            
            # Add all price history
            for price in self._price_history:
                session.add(price.to_db_model(self._db_id))
            
            session.commit()
    
    def add_price_data(self, price_data: OptionPrice) -> None:
        """Add a price data point to the option's history"""
        self._price_history.append(price_data)
    
    def get_price_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[OptionPrice]:
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
    
    def get_latest_price(self) -> Optional[OptionPrice]:
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
                'bid': float(price.bid) if price.bid else None,
                'ask': float(price.ask) if price.ask else None,
                'last': float(price.last) if price.last else None,
                'volume': price.volume,
                'open_interest': price.open_interest,
                'implied_volatility': float(price.implied_volatility) if price.implied_volatility else None,
                'delta': float(price.delta) if price.delta else None,
                'gamma': float(price.gamma) if price.gamma else None,
                'theta': float(price.theta) if price.theta else None,
                'vega': float(price.vega) if price.vega else None,
                'rho': float(price.rho) if price.rho else None
            }
            for price in self._price_history
        ]
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def calculate_break_even(self) -> Optional[Decimal]:
        """Calculate break-even price at expiration"""
        latest = self.get_latest_price()
        if not latest or not latest.mid_price:
            return None
            
        if self.option_type == OptionType.CALL:
            return self.strike_price + latest.mid_price
        else:  # PUT
            return self.strike_price - latest.mid_price
    
    def calculate_intrinsic_value(self, underlying_price: Decimal) -> Decimal:
        """Calculate intrinsic value based on current underlying price"""
        if self.option_type == OptionType.CALL:
            return max(underlying_price - self.strike_price, Decimal('0'))
        else:  # PUT
            return max(self.strike_price - underlying_price, Decimal('0'))
    
    def is_in_the_money(self, underlying_price: Optional[Decimal] = None) -> Optional[bool]:
        """Check if option is in the money"""
        if underlying_price is None:
            latest_stock = self.underlying.get_latest_price()
            if not latest_stock:
                return None
            underlying_price = latest_stock.close
            
        if self.option_type == OptionType.CALL:
            return underlying_price > self.strike_price
        else:  # PUT
            return underlying_price < self.strike_price 