from __future__ import annotations

from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.regime_performance_database import (
    RegimePerformanceDatabase,
    StrategyStateMetrics,
)


class StrategyPerformanceTracker:
    def __init__(self, db: RegimePerformanceDatabase) -> None:
        self.db = db

    def record(self, strategy_id: str, state_hash: str, trade_return: float, drawdown: float, won: bool) -> None:
        cur = self.db.get(strategy_id, state_hash)
        n = cur.trade_count + 1
        new_avg = ((cur.avg_return * cur.trade_count) + trade_return) / n
        win_rate = ((cur.win_rate * cur.trade_count) + (1.0 if won else 0.0)) / n
        sharpe = new_avg / (abs(drawdown) + 1e-6)
        pf = max(new_avg, 0.0) / (abs(min(new_avg, 0.0)) + 1e-6)
        mdd = max(cur.max_drawdown, abs(drawdown))
        self.db.upsert(
            strategy_id,
            state_hash,
            StrategyStateMetrics(
                trade_count=n,
                sharpe=sharpe,
                win_rate=win_rate,
                avg_return=new_avg,
                profit_factor=pf,
                max_drawdown=mdd,
            ),
        )
