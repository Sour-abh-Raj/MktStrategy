from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TradeRiskSettings:
    initial_stoploss: float = -0.06
    trailing_stop: float = 0.02
    breakeven_trigger: float = 0.015
    max_position_size: float = 0.1


class TradeRiskController:
    def __init__(self, settings: TradeRiskSettings | None = None) -> None:
        self.settings = settings or TradeRiskSettings()

    def stoploss_price(self, entry_price: float) -> float:
        return entry_price * (1 + self.settings.initial_stoploss)

    def trailing_stop_price(self, current_price: float) -> float:
        return current_price * (1 - self.settings.trailing_stop)

    def should_move_to_breakeven(self, pnl_pct: float) -> bool:
        return pnl_pct >= self.settings.breakeven_trigger

    def cap_position(self, requested_fraction: float) -> float:
        return min(requested_fraction, self.settings.max_position_size)
