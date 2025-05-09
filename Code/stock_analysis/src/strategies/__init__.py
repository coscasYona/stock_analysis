"""
Trading strategies package for stock analysis
"""

from .base_strategy import BaseStrategy
from .metrics import (
    MetricCategory,
    Metric,
    OptimizationObjective,
    AVAILABLE_METRICS,
    OPTIMIZATION_OBJECTIVES
)
from .optimization import StrategyOptimizer, MultiObjectiveOptimizer 