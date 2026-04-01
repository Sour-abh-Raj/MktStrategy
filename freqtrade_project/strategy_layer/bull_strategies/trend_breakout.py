from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from freqtrade_project.core.indicators import atr, ema, macd_hist, rsi
from freqtrade_project.strategy_layer.strategy_templates.base_regime_strategy import BaseRegimeStrategy


@dataclass
class BullTrendBreakoutConfig:
    ema_fast: int = 12
    ema_slow: int = 36
    rsi_min: float = 55.0
    atr_stop_mult: float = 2.5


class BullTrendBreakoutStrategy(BaseRegimeStrategy):
    strategy_id = "bull_trend_breakout"
    regime_compatibility = "bullish"
    timeframe = "15m"
    stoploss = -0.08
    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.04
    minimal_roi = {"0": 0.08, "30": 0.04, "90": 0.01}

    def __init__(self, config: BullTrendBreakoutConfig | None = None) -> None:
        self.config = config or BullTrendBreakoutConfig()

    def evaluate(self, closes: List[float], highs: List[float], lows: List[float], volumes: List[float]) -> Dict[str, float]:
        if len(closes) < 40:
            return {"enter": 0.0, "exit": 0.0, "atr_stop": 0.0}

        ef = ema(closes, self.config.ema_fast)[-1]
        es = ema(closes, self.config.ema_slow)[-1]
        r = rsi(closes)[-1]
        m = macd_hist(closes)[-1]
        a = atr(highs, lows, closes)[-1]

        breakout = closes[-1] > max(closes[-20:-1])
        volume_boost = volumes[-1] > (sum(volumes[-20:]) / 20) * 1.1

        enter = 1.0 if ef > es and r > self.config.rsi_min and m > 0 and breakout and volume_boost else 0.0
        exit_signal = 1.0 if r > 75 or ef < es or m < 0 else 0.0
        atr_stop = closes[-1] - (a * self.config.atr_stop_mult)
        return {"enter": enter, "exit": exit_signal, "atr_stop": atr_stop}
