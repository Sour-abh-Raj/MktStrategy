from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PortfolioRiskLimits:
    max_portfolio_exposure: float = 0.7
    max_trades_per_pair: int = 2
    max_daily_loss: float = 0.04
    max_drawdown: float = 0.12


class PortfolioRiskController:
    def __init__(self, limits: PortfolioRiskLimits | None = None) -> None:
        self.limits = limits or PortfolioRiskLimits()

    def check(self, exposure: float, trades_by_pair: Dict[str, int], daily_loss: float, drawdown: float) -> Dict[str, bool]:
        return {
            "exposure_ok": exposure <= self.limits.max_portfolio_exposure,
            "trades_ok": all(v <= self.limits.max_trades_per_pair for v in trades_by_pair.values()),
            "daily_loss_ok": daily_loss <= self.limits.max_daily_loss,
            "drawdown_ok": drawdown <= self.limits.max_drawdown,
        }

    def allow_new_trade(self, exposure: float, pair: str, trades_by_pair: Dict[str, int], daily_loss: float, drawdown: float) -> bool:
        checks = self.check(exposure, trades_by_pair, daily_loss, drawdown)
        pair_ok = trades_by_pair.get(pair, 0) < self.limits.max_trades_per_pair
        return all(checks.values()) and pair_ok
