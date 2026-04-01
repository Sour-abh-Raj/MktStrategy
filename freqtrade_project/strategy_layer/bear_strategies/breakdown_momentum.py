from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from freqtrade_project.core.indicators import atr, ema, macd_hist, rsi
from freqtrade_project.strategy_layer.strategy_templates.base_regime_strategy import BaseRegimeStrategy


@dataclass
class BearBreakdownConfig:
    ema_fast: int = 12
    ema_slow: int = 36
    rsi_max: float = 45.0
    atr_stop_mult: float = 2.2


class BearBreakdownMomentumStrategy(BaseRegimeStrategy):
    strategy_id = "bear_breakdown_momentum"
    regime_compatibility = "bearish"
    timeframe = "15m"
    can_short = True
    stoploss = -0.06
    trailing_stop = True
    trailing_stop_positive = 0.018
    trailing_stop_positive_offset = 0.03
    minimal_roi = {"0": 0.07, "20": 0.03, "70": 0.01}

    def __init__(self, config: BearBreakdownConfig | None = None) -> None:
        self.config = config or BearBreakdownConfig()

    def evaluate(self, closes: List[float], highs: List[float], lows: List[float], volumes: List[float]) -> Dict[str, float]:
        if len(closes) < 40:
            return {"enter_short": 0.0, "exit_short": 0.0, "atr_stop": 0.0}

        ef = ema(closes, self.config.ema_fast)[-1]
        es = ema(closes, self.config.ema_slow)[-1]
        r = rsi(closes)[-1]
        m = macd_hist(closes)[-1]
        a = atr(highs, lows, closes)[-1]

        breakdown = closes[-1] < min(closes[-20:-1])
        sell_volume = volumes[-1] > (sum(volumes[-20:]) / 20) * 1.1

        enter_short = 1.0 if ef < es and r < self.config.rsi_max and m < 0 and breakdown and sell_volume else 0.0
        exit_short = 1.0 if r < 25 or ef > es or m > 0 else 0.0
        atr_stop = closes[-1] + (a * self.config.atr_stop_mult)
        return {"enter_short": enter_short, "exit_short": exit_short, "atr_stop": atr_stop}
