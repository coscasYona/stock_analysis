import optuna
from typing import Type, Dict, Any, Optional, Callable
import numpy as np
from .base_strategy import BaseStrategy

class StrategyOptimizer:
    """Class for optimizing trading strategy parameters using Optuna"""
    
    def __init__(
        self,
        strategy_class: Type[BaseStrategy],
        symbol: str,
        optimization_metric: str = 'sharpe_ratio',
        n_trials: int = 100,
        timeout: Optional[int] = None
    ):
        self.strategy_class = strategy_class
        self.symbol = symbol
        self.optimization_metric = optimization_metric
        self.n_trials = n_trials
        self.timeout = timeout
        self.study = None
        self.best_params = None
        self.best_strategy = None
        
    def objective(self, trial: optuna.Trial) -> float:
        """Objective function for Optuna optimization"""
        # Create strategy instance
        strategy = self.strategy_class(symbol=self.symbol)
        
        # Get parameter bounds from strategy
        bounds = strategy.get_optimization_bounds()
        
        # Create parameters dictionary based on bounds
        parameters = {}
        for param_name, (param_type, param_bounds) in bounds.items():
            if param_type == int:
                parameters[param_name] = trial.suggest_int(
                    param_name, param_bounds[0], param_bounds[1]
                )
            elif param_type == float:
                parameters[param_name] = trial.suggest_float(
                    param_name, param_bounds[0], param_bounds[1]
                )
            else:
                raise ValueError(f"Unsupported parameter type: {param_type}")
        
        # Run strategy with suggested parameters
        strategy.set_parameters(parameters)
        strategy.run_strategy()
        metrics = strategy.calculate_metrics()
        
        return metrics[self.optimization_metric]
    
    def optimize(self) -> Dict[str, Any]:
        """Run the optimization process"""
        # Create study object
        self.study = optuna.create_study(
            direction="maximize",
            study_name=f"{self.strategy_class.__name__}_{self.symbol}"
        )
        
        # Run optimization
        self.study.optimize(
            self.objective,
            n_trials=self.n_trials,
            timeout=self.timeout
        )
        
        # Store best parameters
        self.best_params = self.study.best_params
        
        # Create and run strategy with best parameters
        self.best_strategy = self.strategy_class(symbol=self.symbol)
        self.best_strategy.set_parameters(self.best_params)
        self.best_strategy.run_strategy()
        
        return {
            'best_params': self.best_params,
            'best_value': self.study.best_value,
            'best_trial': self.study.best_trial,
            'performance_metrics': self.best_strategy.calculate_metrics()
        }
    
    def plot_optimization_history(self) -> None:
        """Plot the optimization history"""
        if self.study is None:
            raise ValueError("Must run optimize() first")
        optuna.visualization.plot_optimization_history(self.study)
        
    def plot_parameter_importances(self) -> None:
        """Plot parameter importances"""
        if self.study is None:
            raise ValueError("Must run optimize() first")
        optuna.visualization.plot_param_importances(self.study) 