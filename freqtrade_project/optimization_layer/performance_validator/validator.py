from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationThresholds:
    min_sharpe: float = 1.0
    min_profit_factor: float = 1.2
    max_drawdown: float = 0.2


class PerformanceValidator:
    def __init__(self, thresholds: ValidationThresholds | None = None) -> None:
        self.thresholds = thresholds or ValidationThresholds()

    def validate(self, sharpe: float, profit_factor: float, max_drawdown: float) -> bool:
        return (
            sharpe >= self.thresholds.min_sharpe
            and profit_factor >= self.thresholds.min_profit_factor
            and max_drawdown <= self.thresholds.max_drawdown
        )
