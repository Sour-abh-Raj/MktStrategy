from __future__ import annotations

from dataclasses import dataclass

from freqtrade_project.strategy_layer.strategy_evolution_engine.strategy_generator import (
    CandidateStrategy,
)


@dataclass
class FitnessResult:
    candidate: CandidateStrategy
    score: float
    sharpe: float
    sortino: float
    profit_factor: float
    drawdown: float
    win_rate: float


class FitnessEvaluator:
    """Enhanced fitness evaluator for strategy evolution."""

    def __init__(self, ranking_method: str = "risk_adjusted"):
        self.ranking_method = ranking_method

    def evaluate(
        self,
        candidate: CandidateStrategy,
        sharpe: float,
        drawdown: float,
        win_rate: float,
        sortino: float = 0.0,
        profit_factor: float = 1.0,
    ) -> FitnessResult:
        """Evaluate strategy fitness using comprehensive metrics."""

        if self.ranking_method == "risk_adjusted":
            # Balanced risk-adjusted scoring
            score = (
                0.35 * sharpe
                + 0.25 * sortino
                + 0.20 * profit_factor
                - 0.15 * drawdown
                + 0.10 * win_rate
            )
        elif self.ranking_method == "conservative":
            # Conservative: prioritize risk control
            score = (
                0.25 * sharpe
                + 0.20 * sortino
                + 0.15 * profit_factor
                - 0.30 * drawdown
                + 0.10 * win_rate
            )
        elif self.ranking_method == "aggressive":
            # Aggressive: prioritize returns
            score = (
                0.40 * sharpe
                + 0.25 * sortino
                + 0.25 * profit_factor
                - 0.08 * drawdown
                + 0.10 * win_rate
            )
        else:
            # Default risk-adjusted
            score = (
                0.35 * sharpe
                + 0.25 * sortino
                + 0.20 * profit_factor
                - 0.15 * drawdown
                + 0.10 * win_rate
            )

        return FitnessResult(
            candidate=candidate,
            score=round(score, 4),
            sharpe=round(sharpe, 4),
            sortino=round(sortino, 4),
            profit_factor=round(profit_factor, 4),
            drawdown=round(drawdown, 4),
            win_rate=round(win_rate, 4),
        )
