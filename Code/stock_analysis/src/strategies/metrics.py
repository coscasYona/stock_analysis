from typing import Dict, Any, List, Callable, Optional
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum, auto

class MetricCategory(Enum):
    """Categories for grouping metrics"""
    RETURNS = auto()
    RISK = auto()
    RATIOS = auto()
    TRADES = auto()
    POSITION = auto()

@dataclass
class Metric:
    """Class representing a performance metric"""
    name: str
    description: str
    category: MetricCategory
    higher_is_better: bool
    requires_columns: list[str]
    calculation_function: Callable[[pd.DataFrame], float]

@dataclass
class OptimizationObjective:
    """Class representing an optimization objective"""
    name: str
    description: str
    higher_is_better: bool
    metric_name: str

class Metrics:
    """Collection of trading strategy performance metrics"""
    
    @staticmethod
    def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sortino ratio (only penalizes downside volatility)"""
        excess_returns = returns - risk_free_rate
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return np.inf
        return np.sqrt(252) * excess_returns.mean() / downside_returns.std()
    
    @staticmethod
    def calculate_calmar_ratio(returns: pd.Series, prices: pd.Series) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)"""
        annual_return = (1 + returns.mean()) ** 252 - 1
        max_dd = Metrics.calculate_max_drawdown(prices)
        return abs(annual_return / max_dd) if max_dd != 0 else np.inf
    
    @staticmethod
    def calculate_max_drawdown(prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        peak = prices.expanding(min_periods=1).max()
        drawdown = (prices - peak) / peak
        return drawdown.min()
    
    @staticmethod
    def calculate_win_rate(returns: pd.Series) -> float:
        """Calculate win rate (percentage of profitable trades)"""
        return (returns > 0).mean()
    
    @staticmethod
    def calculate_profit_factor(returns: pd.Series) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        gains = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        return gains / losses if losses != 0 else np.inf
    
    @staticmethod
    def calculate_expectancy(returns: pd.Series) -> float:
        """Calculate expectancy (average gain/loss per trade)"""
        return returns.mean()
    
    @staticmethod
    def calculate_recovery_factor(returns: pd.Series, prices: pd.Series) -> float:
        """Calculate recovery factor (total return / max drawdown)"""
        total_return = (1 + returns).prod() - 1
        max_dd = Metrics.calculate_max_drawdown(prices)
        return abs(total_return / max_dd) if max_dd != 0 else np.inf
    
    @staticmethod
    def calculate_ulcer_index(prices: pd.Series) -> float:
        """Calculate Ulcer Index (measure of downside risk)"""
        peak = prices.expanding(min_periods=1).max()
        drawdown = (prices - peak) / peak
        return np.sqrt(np.mean(drawdown ** 2))
    
    @staticmethod
    def calculate_omega_ratio(returns: pd.Series, threshold: float = 0.0) -> float:
        """Calculate Omega ratio (probability weighted ratio of gains vs losses)"""
        gains = returns[returns > threshold].sum()
        losses = abs(returns[returns <= threshold].sum())
        return gains / losses if losses != 0 else np.inf

def calculate_sharpe_ratio(df: pd.DataFrame) -> float:
    """Calculate Sharpe ratio"""
    returns = df['returns']
    if len(returns) < 2:
        return 0.0
    return np.sqrt(252) * returns.mean() / returns.std()

def calculate_sortino_ratio(df: pd.DataFrame) -> float:
    """Calculate Sortino ratio"""
    returns = df['returns']
    if len(returns) < 2:
        return 0.0
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0:
        return float('inf')
    return np.sqrt(252) * returns.mean() / downside_returns.std()

def calculate_max_drawdown(df: pd.DataFrame) -> float:
    """Calculate maximum drawdown"""
    cumulative_returns = (1 + df['returns']).cumprod()
    rolling_max = cumulative_returns.expanding().max()
    drawdowns = cumulative_returns / rolling_max - 1
    return abs(drawdowns.min())

def calculate_win_rate(df: pd.DataFrame) -> float:
    """Calculate win rate"""
    if 'trade_returns' not in df.columns or len(df['trade_returns']) == 0:
        return 0.0
    winning_trades = (df['trade_returns'] > 0).sum()
    total_trades = len(df['trade_returns'].dropna())
    return winning_trades / total_trades if total_trades > 0 else 0.0

def calculate_profit_factor(df: pd.DataFrame) -> float:
    """Calculate profit factor"""
    if 'trade_returns' not in df.columns or len(df['trade_returns']) == 0:
        return 0.0
    gains = df['trade_returns'][df['trade_returns'] > 0].sum()
    losses = abs(df['trade_returns'][df['trade_returns'] < 0].sum())
    return gains / losses if losses != 0 else float('inf')

def calculate_average_trade(df: pd.DataFrame) -> float:
    """Calculate average trade return"""
    if 'trade_returns' not in df.columns or len(df['trade_returns']) == 0:
        return 0.0
    return df['trade_returns'].mean()

def calculate_average_position_size(df: pd.DataFrame) -> float:
    """Calculate average position size"""
    if 'position_size' not in df.columns:
        return 0.0
    return df['position_size'].abs().mean()

# Define available metrics
AVAILABLE_METRICS: Dict[str, Metric] = {
    'sharpe_ratio': Metric(
        name='Sharpe Ratio',
        description='Risk-adjusted return using standard deviation of returns',
        category=MetricCategory.RATIOS,
        higher_is_better=True,
        requires_columns=['returns'],
        calculation_function=calculate_sharpe_ratio
    ),
    'sortino_ratio': Metric(
        name='Sortino Ratio',
        description='Risk-adjusted return using downside deviation',
        category=MetricCategory.RATIOS,
        higher_is_better=True,
        requires_columns=['returns'],
        calculation_function=calculate_sortino_ratio
    ),
    'max_drawdown': Metric(
        name='Maximum Drawdown',
        description='Maximum peak to trough decline',
        category=MetricCategory.RISK,
        higher_is_better=False,
        requires_columns=['returns'],
        calculation_function=calculate_max_drawdown
    ),
    'win_rate': Metric(
        name='Win Rate',
        description='Percentage of winning trades',
        category=MetricCategory.TRADES,
        higher_is_better=True,
        requires_columns=['trade_returns'],
        calculation_function=calculate_win_rate
    ),
    'profit_factor': Metric(
        name='Profit Factor',
        description='Ratio of gross profits to gross losses',
        category=MetricCategory.TRADES,
        higher_is_better=True,
        requires_columns=['trade_returns'],
        calculation_function=calculate_profit_factor
    ),
    'average_trade': Metric(
        name='Average Trade',
        description='Average return per trade',
        category=MetricCategory.TRADES,
        higher_is_better=True,
        requires_columns=['trade_returns'],
        calculation_function=calculate_average_trade
    ),
    'average_position_size': Metric(
        name='Average Position Size',
        description='Average absolute position size',
        category=MetricCategory.POSITION,
        higher_is_better=None,  # Neither better nor worse
        requires_columns=['position_size'],
        calculation_function=calculate_average_position_size
    )
}

# Define optimization objectives
OPTIMIZATION_OBJECTIVES: Dict[str, OptimizationObjective] = {
    'sharpe_ratio': OptimizationObjective(
        name='Maximize Sharpe Ratio',
        description='Optimize for risk-adjusted returns',
        higher_is_better=True,
        metric_name='sharpe_ratio'
    ),
    'sortino_ratio': OptimizationObjective(
        name='Maximize Sortino Ratio',
        description='Optimize for downside risk-adjusted returns',
        higher_is_better=True,
        metric_name='sortino_ratio'
    ),
    'max_drawdown': OptimizationObjective(
        name='Minimize Maximum Drawdown',
        description='Optimize for capital preservation',
        higher_is_better=False,
        metric_name='max_drawdown'
    ),
    'profit_factor': OptimizationObjective(
        name='Maximize Profit Factor',
        description='Optimize for trade profitability',
        higher_is_better=True,
        metric_name='profit_factor'
    )
} 