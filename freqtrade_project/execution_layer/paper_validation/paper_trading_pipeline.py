from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Iterable, List

from freqtrade_project.pipeline import AdaptiveTradingSystem, CycleInput


@dataclass
class PaperTradingPlan:
    start_date: date
    end_date: date
    days: int


@dataclass
class PaperTradingResult:
    days: int
    cycles: int
    executed_orders: int
    active_cycles: int


class PaperTradingValidationPipeline:
    def build_plan(self, start_date: date, days: int = 45) -> PaperTradingPlan:
        if days < 30 or days > 60:
            raise ValueError("Paper trading window must be between 30 and 60 days.")
        return PaperTradingPlan(start_date=start_date, end_date=start_date + timedelta(days=days), days=days)

    def simulate(self, pair: str, timeframe: str, daily_rows: Iterable[List[dict]], initial_equity: float = 10000) -> PaperTradingResult:
        system = AdaptiveTradingSystem()
        cycles = 0
        executed_orders = 0
        active_cycles = 0
        equity = initial_equity

        for rows in daily_rows:
            cycles += 1
            result = system.run_cycle(
                CycleInput(
                    pair=pair,
                    timeframe=timeframe,
                    raw_rows=rows,
                    tf_scores={"1d": 0.1, "4h": 0.1, "15m": 0.1},
                    stress_metrics={
                        "volatility_current": 0.02,
                        "volatility_average": 0.02,
                        "price_change_5m": 0.0,
                        "price_change_15m": 0.0,
                        "spread": 0.001,
                        "spread_avg": 0.001,
                        "volume_ratio": 1.0,
                        "portfolio_drawdown": 0.0,
                        "api_errors": 0,
                    },
                    equity=equity,
                )
            )
            orders = len(result.get("execution", []))
            executed_orders += orders
            active_cycles += int(orders > 0)

        return PaperTradingResult(days=cycles, cycles=cycles, executed_orders=executed_orders, active_cycles=active_cycles)
