"""
Strategy Expansion - New Strategy Families and Optimization

Modules:
- strategy_expander.py: New strategy families (breakout, market structure, stat arb, multi-tf, regime)
- parameter_optimizer.py: Hyperparameter optimization (Bayesian, genetic, adaptive)
- portfolio_optimizer.py: Portfolio allocation (risk parity, vol scaling, Sharpe-weighted, hierarchical)
- alpha_decay_monitor.py: Alpha decay detection and strategy retirement
- continuous_improvement.py: Integration of all modules into improvement loop
"""

from freqtrade_project.strategy_layer.strategy_expansion.strategy_expander import (
    StrategyExpander,
    StrategyFamily,
    ExpandedStrategy,
    BreakoutConfig,
    MarketStructureConfig,
    StatArbConfig,
    MultiTimeframeConfig,
    RegimeSpecificConfig,
    create_strategy_expander,
)

from freqtrade_project.strategy_layer.strategy_expansion.parameter_optimizer import (
    ParameterOptimizer,
    ParameterSpace,
    OptimizedParameters,
    OptimizationResult,
    AdaptiveParameterSearch,
    create_parameter_optimizer,
)

from freqtrade_project.strategy_layer.strategy_expansion.portfolio_optimizer import (
    PortfolioOptimizer,
    PortfolioMetrics,
    AllocationResult,
    create_portfolio_optimizer,
)

from freqtrade_project.strategy_layer.strategy_expansion.alpha_decay_monitor import (
    AlphaDecayMonitor,
    DecayMetrics,
    DecayAlert,
    DecayReport,
    create_decay_monitor,
)

from freqtrade_project.strategy_layer.strategy_expansion.continuous_improvement import (
    ContinuousImprovementEngine,
    ImprovementCycle,
    ImprovementReport,
    create_improvement_engine,
)

__all__ = [
    # Strategy expansion
    "StrategyExpander",
    "StrategyFamily",
    "ExpandedStrategy",
    "BreakoutConfig",
    "MarketStructureConfig",
    "StatArbConfig",
    "MultiTimeframeConfig",
    "RegimeSpecificConfig",
    "create_strategy_expander",
    
    # Parameter optimization
    "ParameterOptimizer",
    "ParameterSpace",
    "OptimizedParameters",
    "OptimizationResult",
    "AdaptiveParameterSearch",
    "create_parameter_optimizer",
    
    # Portfolio optimization
    "PortfolioOptimizer",
    "PortfolioMetrics",
    "AllocationResult",
    "create_portfolio_optimizer",
    
    # Alpha decay
    "AlphaDecayMonitor",
    "DecayMetrics",
    "DecayAlert",
    "DecayReport",
    "create_decay_monitor",
    
    # Continuous improvement
    "ContinuousImprovementEngine",
    "ImprovementCycle",
    "ImprovementReport",
    "create_improvement_engine",
]
