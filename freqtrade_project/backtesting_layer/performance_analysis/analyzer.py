from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import List


@dataclass
class PerformanceMetrics:
    sharpe: float
    sortino: float
    max_drawdown: float
    profit_factor: float
    win_rate: float


class PerformanceAnalyzer:
    def analyze(self, returns: List[float]) -> PerformanceMetrics:
        if not returns:
            return PerformanceMetrics(0, 0, 1, 0, 0)

        avg = mean(returns)
        vol = pstdev(returns) if len(returns) > 1 else 0.0
        downside = [r for r in returns if r < 0]
        dvol = pstdev(downside) if len(downside) > 1 else (abs(mean(downside)) if downside else 0.0)

        equity = 1.0
        peak = 1.0
        max_dd = 0.0
        gross_profit = 0.0
        gross_loss = 0.0
        wins = 0
        for r in returns:
            equity *= 1 + r
            peak = max(peak, equity)
            max_dd = max(max_dd, (peak - equity) / peak)
            wins += int(r > 0)
            if r > 0:
                gross_profit += r
            else:
                gross_loss += abs(r)

        sharpe = avg / vol if vol > 0 else 0.0
        sortino = avg / dvol if dvol > 0 else 0.0
        pf = gross_profit / gross_loss if gross_loss > 0 else gross_profit
        return PerformanceMetrics(sharpe=sharpe, sortino=sortino, max_drawdown=max_dd, profit_factor=pf, win_rate=wins / len(returns))
