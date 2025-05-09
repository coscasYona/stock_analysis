from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
from .metrics import AVAILABLE_METRICS, MetricCategory

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.data = None
        self.performance_metrics = {}
        
    @abstractmethod
    def run_strategy(self, **kwargs) -> None:
        """Run the strategy with given parameters"""
        pass
        
    @abstractmethod
    def plot_strategy(self) -> None:
        """Plot the strategy results"""
        pass
    
    def calculate_metrics(self, metrics_list: Optional[List[str]] = None) -> Dict[str, float]:
        """Calculate performance metrics for the strategy"""
        if self.data is None or 'Signal' not in self.data.columns:
            raise ValueError("Strategy must be run before calculating metrics")
            
        # Calculate returns if not already present
        if 'Returns' not in self.data.columns:
            self.data['Returns'] = self.data['Close'].pct_change()
        if 'Strategy_Returns' not in self.data.columns:
            self.data['Strategy_Returns'] = self.data['Signal'].shift(1) * self.data['Returns']
        
        # If no metrics specified, calculate all available metrics
        if metrics_list is None:
            metrics_list = list(AVAILABLE_METRICS.keys())
        
        # Calculate specified metrics
        for metric_name in metrics_list:
            if metric_name not in AVAILABLE_METRICS:
                raise ValueError(f"Unknown metric: {metric_name}")
                
            metric = AVAILABLE_METRICS[metric_name]
            
            # Check if required data columns are present
            missing_columns = [col for col in metric.requires if col not in self.data.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns for {metric_name}: {missing_columns}")
            
            # Calculate metric
            try:
                self.performance_metrics[metric_name] = metric.function(self.data)
            except Exception as e:
                self.performance_metrics[metric_name] = None
                print(f"Warning: Failed to calculate {metric_name}: {str(e)}")
        
        return self.performance_metrics
    
    def get_metrics_by_category(self, category: MetricCategory) -> Dict[str, float]:
        """Get metrics filtered by category"""
        if not self.performance_metrics:
            self.calculate_metrics()
            
        return {
            name: value 
            for name, value in self.performance_metrics.items()
            if AVAILABLE_METRICS[name].category == category
        }
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get the current parameters of the strategy"""
        pass
    
    @abstractmethod
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set new parameters for the strategy"""
        pass
    
    def get_optimization_bounds(self) -> Dict[str, tuple]:
        """Get the bounds for parameter optimization"""
        raise NotImplementedError("Optimization bounds must be defined in the concrete strategy class") 