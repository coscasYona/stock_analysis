from typing import List, Dict, Any, Type
import pandas as pd
import matplotlib.pyplot as plt
from .base_strategy import BaseStrategy
from .strategy_optimizer import StrategyOptimizer
from .metrics import MetricCategory

class StrategyComparison:
    """Class for comparing multiple trading strategies"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.strategies = {}
        self.results = {}
        
    def add_strategy(
        self,
        strategy_class: Type[BaseStrategy],
        name: str,
        parameters: Dict[str, Any] = None,
        optimize: bool = False,
        optimization_metric: str = 'sharpe_ratio',
        n_trials: int = 100
    ) -> None:
        """Add a strategy to the comparison"""
        if optimize:
            # Optimize strategy parameters
            optimizer = StrategyOptimizer(
                strategy_class=strategy_class,
                symbol=self.symbol,
                optimization_metric=optimization_metric,
                n_trials=n_trials
            )
            optimization_results = optimizer.optimize()
            strategy = optimizer.best_strategy
            self.results[name] = {
                'strategy': strategy,
                'metrics': optimization_results['performance_metrics'],
                'optimization_results': optimization_results
            }
        else:
            # Use provided parameters
            strategy = strategy_class(symbol=self.symbol)
            if parameters:
                strategy.set_parameters(parameters)
            strategy.run_strategy()
            self.results[name] = {
                'strategy': strategy,
                'metrics': strategy.calculate_metrics(),
                'optimization_results': None
            }
        
        self.strategies[name] = strategy
    
    def compare_metrics(self) -> pd.DataFrame:
        """Compare performance metrics across strategies"""
        metrics_dict = {}
        for name, result in self.results.items():
            metrics_dict[name] = result['metrics']
        return pd.DataFrame(metrics_dict).T
    
    def plot_returns_comparison(self, save_path: str = None) -> None:
        """Plot cumulative returns comparison"""
        plt.figure(figsize=(14, 7))
        
        for name, strategy in self.strategies.items():
            cumulative_returns = (1 + strategy.data['Strategy_Returns']).cumprod()
            plt.plot(cumulative_returns.index, cumulative_returns.values, label=name)
        
        plt.title(f'Strategy Comparison - Cumulative Returns ({self.symbol})')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Return')
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path, dpi=300)
            plt.close()
        else:
            plt.show()
    
    def plot_drawdown_comparison(self, save_path: str = None) -> None:
        """Plot drawdown comparison"""
        plt.figure(figsize=(14, 7))
        
        for name, strategy in self.strategies.items():
            # Calculate drawdown
            cumulative_returns = (1 + strategy.data['Strategy_Returns']).cumprod()
            running_max = cumulative_returns.expanding(min_periods=1).max()
            drawdown = (cumulative_returns - running_max) / running_max
            
            plt.plot(drawdown.index, drawdown.values, label=name)
        
        plt.title(f'Strategy Comparison - Drawdown ({self.symbol})')
        plt.xlabel('Date')
        plt.ylabel('Drawdown')
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path, dpi=300)
            plt.close()
        else:
            plt.show()
    
    def get_optimization_results(self, strategy_name: str) -> Dict[str, Any]:
        """Get optimization results for a specific strategy"""
        if strategy_name not in self.results:
            raise ValueError(f"Strategy '{strategy_name}' not found")
        return self.results[strategy_name].get('optimization_results') 