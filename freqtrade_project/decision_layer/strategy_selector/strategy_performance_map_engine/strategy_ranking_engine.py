from __future__ import annotations

from typing import List, Tuple

from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.regime_performance_database import (
    RegimePerformanceDatabase,
)


class StrategyRankingEngine:
    def __init__(self, db: RegimePerformanceDatabase, min_trades: int = 20, min_fitness: float = 0.1) -> None:
        self.db = db
        self.min_trades = min_trades
        self.min_fitness = min_fitness

    @staticmethod
    def fitness(sharpe: float, profit_factor: float, drawdown: float, win_rate: float) -> float:
        return (0.4 * sharpe) + (0.3 * profit_factor) - (0.2 * drawdown) + (0.1 * win_rate)

    def rank(self, state_hash: str) -> List[Tuple[str, float]]:
        rows = self.db.all_for_state(state_hash)
        ranked: List[Tuple[str, float]] = []
        for strategy_id, m in rows.items():
            if m.trade_count < self.min_trades:
                continue
            f = self.fitness(m.sharpe, m.profit_factor, m.max_drawdown, m.win_rate)
            if f >= self.min_fitness:
                ranked.append((strategy_id, round(f, 4)))
        return sorted(ranked, key=lambda x: x[1], reverse=True)
