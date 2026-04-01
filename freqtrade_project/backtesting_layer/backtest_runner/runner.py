from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from freqtrade_project.backtesting_layer.performance_analysis.analyzer import PerformanceAnalyzer, PerformanceMetrics


@dataclass
class BacktestReport:
    metrics: PerformanceMetrics
    total_return: float
    average_trade_return: float
    trade_frequency: float
    regime_breakdown: Dict[str, PerformanceMetrics]


class BacktestRunner:
    def __init__(self) -> None:
        self.analyzer = PerformanceAnalyzer()

    def evaluate(self, returns: List[float], regime_returns: Dict[str, List[float]] | None = None) -> BacktestReport:
        metrics = self.analyzer.analyze(returns)
        total_return = 1.0
        for r in returns:
            total_return *= 1 + r
        total_return -= 1
        regime_breakdown = {k: self.analyzer.analyze(v) for k, v in (regime_returns or {}).items()}
        return BacktestReport(
            metrics=metrics,
            total_return=total_return,
            average_trade_return=(sum(returns) / len(returns)) if returns else 0.0,
            trade_frequency=len(returns),
            regime_breakdown=regime_breakdown,
        )
