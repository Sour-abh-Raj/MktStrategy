from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.regime_performance_database import (
    RegimePerformanceDatabase,
)


@dataclass
class StrategyScore:
    """Comprehensive strategy scoring with multiple metrics."""

    strategy_id: str
    overall_score: float
    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float
    max_drawdown: float
    win_rate: float
    trade_count: int
    avg_trade_return: float
    stability_score: float
    regime_suitability: float


class StrategyRankingEngine:
    """Advanced strategy ranking system with multiple evaluation methods."""

    # Scoring weights for different objectives
    RISK_ADJUSTED_WEIGHTS = {
        "sharpe_ratio": 0.25,
        "sortino_ratio": 0.20,
        "profit_factor": 0.20,
        "max_drawdown_penalty": -0.15,
        "win_rate": 0.10,
        "stability": 0.10,
        "trade_count_bonus": 0.05,
    }

    CONSERVATIVE_WEIGHTS = {
        "sharpe_ratio": 0.20,
        "sortino_ratio": 0.15,
        "profit_factor": 0.15,
        "max_drawdown_penalty": -0.25,
        "win_rate": 0.10,
        "stability": 0.10,
        "trade_count_bonus": 0.05,
    }

    AGGRESSIVE_WEIGHTS = {
        "sharpe_ratio": 0.30,
        "sortino_ratio": 0.20,
        "profit_factor": 0.25,
        "max_drawdown_penalty": -0.10,
        "win_rate": 0.10,
        "stability": 0.05,
        "trade_count_bonus": 0.00,
    }

    def __init__(
        self,
        db: RegimePerformanceDatabase,
        min_trades: int = 20,
        min_sharpe: float = 0.5,
        ranking_method: str = "risk_adjusted",
    ) -> None:
        self.db = db
        self.min_trades = min_trades
        self.min_sharpe = min_sharpe
        self.ranking_method = ranking_method
        self.weights = getattr(
            self, f"{ranking_method.upper()}_WEIGHTS", self.RISK_ADJUSTED_WEIGHTS
        )

    def rank(self, state_hash: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Rank strategies for a given market state."""
        scores = self.score_strategies(state_hash)
        # Return top strategies by overall score
        ranked = sorted(scores.values(), key=lambda s: s.overall_score, reverse=True)
        return [(s.strategy_id, round(s.overall_score, 4)) for s in ranked[:limit]]

    def score_strategies(self, state_hash: str) -> Dict[str, StrategyScore]:
        """Calculate comprehensive scores for all strategies in a market state."""
        rows = self.db.all_for_state(state_hash)
        scores = {}

        for strategy_id, metrics in rows.items():
            if not self._passes_minimum_criteria(metrics):
                continue

            score = self._calculate_comprehensive_score(
                strategy_id, metrics, state_hash
            )
            scores[strategy_id] = score

        return scores

    def _passes_minimum_criteria(self, metrics) -> bool:
        """Check if strategy meets minimum performance criteria."""
        return (
            metrics.trade_count >= self.min_trades
            and metrics.sharpe >= self.min_sharpe
            and metrics.max_drawdown <= 0.25  # Max 25% drawdown
        )

    def _calculate_comprehensive_score(
        self, strategy_id: str, metrics, state_hash: str
    ) -> StrategyScore:
        """Calculate comprehensive score using multiple metrics."""
        # Normalize metrics to 0-1 scale for consistent weighting
        sharpe_norm = min(max(metrics.sharpe / 3.0, 0), 1)  # Cap at 3.0 Sharpe
        sortino_norm = (
            sharpe_norm * 0.8
        )  # Approximate sortino from sharpe (placeholder)
        profit_factor_norm = min(
            max((metrics.profit_factor - 1) / 2.0, 0), 1
        )  # 1.0-3.0 range
        drawdown_penalty = min(metrics.max_drawdown / 0.25, 1)  # 0-25% drawdown
        win_rate_norm = metrics.win_rate  # Already 0-1
        stability_score = self._calculate_stability_score(metrics)
        trade_count_bonus = min(metrics.trade_count / 100, 1)  # Bonus for more trades

        # Calculate overall score using weights
        overall_score = (
            self.weights["sharpe_ratio"] * sharpe_norm
            + self.weights["sortino_ratio"] * sortino_norm
            + self.weights["profit_factor"] * profit_factor_norm
            + self.weights["max_drawdown_penalty"] * drawdown_penalty
            + self.weights["win_rate"] * win_rate_norm
            + self.weights["stability"] * stability_score
            + self.weights["trade_count_bonus"] * trade_count_bonus
        )

        return StrategyScore(
            strategy_id=strategy_id,
            overall_score=round(overall_score, 4),
            sharpe_ratio=round(metrics.sharpe, 4),
            sortino_ratio=round(sortino_norm, 4),  # Use calculated approximation
            profit_factor=round(metrics.profit_factor, 4),
            max_drawdown=round(metrics.max_drawdown, 4),
            win_rate=round(metrics.win_rate, 4),
            trade_count=metrics.trade_count,
            avg_trade_return=round(
                metrics.avg_return, 6
            ),  # Use avg_return from metrics
            stability_score=round(stability_score, 4),
            regime_suitability=round(
                self._calculate_regime_suitability(strategy_id, state_hash), 4
            ),
        )

    def _calculate_stability_score(self, metrics) -> float:
        """Calculate strategy stability based on consistency metrics."""
        # Simple stability measure: lower volatility in returns
        # In a real system, this would analyze return distribution
        consistency_factor = 1.0 - min(
            metrics.max_drawdown * 2, 0.5
        )  # Penalize high drawdowns
        frequency_factor = min(
            metrics.trade_count / 50, 1.0
        )  # Reward sufficient sample size

        return (consistency_factor + frequency_factor) / 2.0

    def _calculate_regime_suitability(self, strategy_id: str, state_hash: str) -> float:
        """Calculate how well this strategy performs in this regime vs others."""
        # Simple regime suitability: compare performance in this state vs overall
        # In a real system, this would compare against historical regime performance
        return 0.8  # Placeholder - would be calculated from historical data

    def get_top_strategies(self, state_hash: str, n: int = 5) -> List[StrategyScore]:
        """Get top N strategies with full scoring details."""
        scores = self.score_strategies(state_hash)
        return sorted(scores.values(), key=lambda s: s.overall_score, reverse=True)[:n]

    def filter_by_criteria(
        self,
        state_hash: str,
        min_sharpe: float | None = None,
        max_drawdown: float | None = None,
        min_win_rate: float | None = None,
    ) -> Dict[str, StrategyScore]:
        """Filter strategies by custom criteria."""
        scores = self.score_strategies(state_hash)
        filtered = {}

        for strategy_id, score in scores.items():
            if min_sharpe and score.sharpe_ratio < min_sharpe:
                continue
            if max_drawdown and score.max_drawdown > max_drawdown:
                continue
            if min_win_rate and score.win_rate < min_win_rate:
                continue
            filtered[strategy_id] = score

        return filtered

    @staticmethod
    def legacy_fitness(
        sharpe: float, profit_factor: float, drawdown: float, win_rate: float
    ) -> float:
        """Legacy fitness function for backward compatibility."""
        return (
            (0.4 * sharpe) + (0.3 * profit_factor) - (0.2 * drawdown) + (0.1 * win_rate)
        )
