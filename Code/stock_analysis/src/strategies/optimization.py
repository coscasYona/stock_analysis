from typing import Dict, Any, Callable, List, Optional
import optuna
from .metrics import AVAILABLE_METRICS, OPTIMIZATION_OBJECTIVES

class StrategyOptimizer:
    """Class for optimizing strategy parameters using Optuna"""
    
    def __init__(self, strategy_class, symbol: str, objective_name: str = 'sharpe_ratio',
                 additional_metrics: Optional[List[str]] = None):
        self.strategy_class = strategy_class
        self.symbol = symbol
        
        if objective_name not in OPTIMIZATION_OBJECTIVES:
            raise ValueError(f"Unknown optimization objective: {objective_name}")
        self.objective_name = objective_name
        self.objective_function = OPTIMIZATION_OBJECTIVES[objective_name]
        self.additional_metrics = additional_metrics or []
        
    def create_trial_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        """Create parameters for a trial based on strategy's optimization bounds"""
        strategy = self.strategy_class(self.symbol)
        bounds = strategy.get_optimization_bounds()
        
        params = {}
        for param_name, (param_type, *bounds_values) in bounds.items():
            if param_type == 'int':
                params[param_name] = trial.suggest_int(param_name, *bounds_values)
            elif param_type == 'float':
                params[param_name] = trial.suggest_float(param_name, *bounds_values)
            elif param_type == 'categorical':
                params[param_name] = trial.suggest_categorical(param_name, bounds_values[0])
            else:
                raise ValueError(f"Unknown parameter type: {param_type}")
                
        return params
        
    def objective(self, trial: optuna.Trial) -> float:
        """Optimization objective function"""
        # Create strategy instance and set parameters
        strategy = self.strategy_class(self.symbol)
        params = self.create_trial_params(trial)
        strategy.set_parameters(params)
        
        # Run strategy
        try:
            strategy.run_strategy()
        except Exception as e:
            print(f"Strategy run failed with parameters {params}: {str(e)}")
            return float('-inf')
            
        # Calculate metrics
        metrics_to_calculate = [self.objective_name] + self.additional_metrics
        metrics = strategy.calculate_metrics(metrics_to_calculate)
        
        # Store additional metrics as trial user attributes
        for metric_name in self.additional_metrics:
            if metric_name in metrics:
                trial.set_user_attr(metric_name, metrics[metric_name])
                
        return metrics.get(self.objective_name, float('-inf'))
        
    def optimize(self, n_trials: int = 100, timeout: Optional[int] = None,
                direction: str = 'maximize') -> optuna.Study:
        """Run the optimization process"""
        study = optuna.create_study(direction=direction)
        study.optimize(self.objective, n_trials=n_trials, timeout=timeout)
        
        return study
        
    @staticmethod
    def get_available_objectives() -> Dict[str, str]:
        """Get dictionary of available optimization objectives with descriptions"""
        return {
            name: obj.description 
            for name, obj in OPTIMIZATION_OBJECTIVES.items()
        }
        
class MultiObjectiveOptimizer(StrategyOptimizer):
    """Class for multi-objective optimization of strategy parameters"""
    
    def __init__(self, strategy_class, symbol: str, objectives: List[str]):
        if not objectives:
            raise ValueError("At least one objective must be specified")
            
        for obj in objectives:
            if obj not in OPTIMIZATION_OBJECTIVES:
                raise ValueError(f"Unknown optimization objective: {obj}")
                
        super().__init__(strategy_class, symbol, objectives[0])
        self.objectives = objectives
        
    def objective(self, trial: optuna.Trial) -> List[float]:
        """Multi-objective optimization function"""
        # Create strategy instance and set parameters
        strategy = self.strategy_class(self.symbol)
        params = self.create_trial_params(trial)
        strategy.set_parameters(params)
        
        # Run strategy
        try:
            strategy.run_strategy()
        except Exception as e:
            print(f"Strategy run failed with parameters {params}: {str(e)}")
            return [float('-inf')] * len(self.objectives)
            
        # Calculate metrics
        metrics = strategy.calculate_metrics(self.objectives)
        
        # Return list of objective values
        return [metrics.get(obj, float('-inf')) for obj in self.objectives]
        
    def optimize(self, n_trials: int = 100, timeout: Optional[int] = None) -> optuna.Study:
        """Run the multi-objective optimization process"""
        directions = ['maximize' if OPTIMIZATION_OBJECTIVES[obj].higher_is_better else 'minimize'
                     for obj in self.objectives]
        study = optuna.create_study(directions=directions)
        study.optimize(self.objective, n_trials=n_trials, timeout=timeout)
        
        return study 