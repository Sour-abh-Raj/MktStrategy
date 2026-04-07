"""
Testing Layer - Pre-Deployment Robustness Testing

Modules:
- engine.py: Complete testing engine
- walk_forward.py: Walk-forward validation
- monte_carlo.py: Monte Carlo robustness testing
- stress_testing.py: Stress scenario testing
"""

from freqtrade_project.testing_layer.engine import (
    TestingEngine,
    TestConfig,
    StrategyTestResult,
    BenchmarkComparison,
    SystemTestSummary,
    create_testing_engine,
)

from freqtrade_project.testing_layer.walk_forward import (
    WalkForwardValidator,
    WalkForwardResult,
    create_walk_forward_validator,
)

from freqtrade_project.testing_layer.monte_carlo import (
    MonteCarloSimulator,
    MonteCarloResult,
    create_monte_carlo_simulator,
)

from freqtrade_project.testing_layer.stress_testing import (
    StressTester,
    StressTestSummary,
    CrisisSimulator,
    create_stress_tester,
)

__all__ = [
    "TestingEngine",
    "TestConfig",
    "StrategyTestResult",
    "BenchmarkComparison",
    "SystemTestSummary",
    "create_testing_engine",
    "WalkForwardValidator",
    "WalkForwardResult",
    "create_walk_forward_validator",
    "MonteCarloSimulator",
    "MonteCarloResult",
    "create_monte_carlo_simulator",
    "StressTester",
    "StressTestSummary",
    "CrisisSimulator",
    "create_stress_tester",
]
