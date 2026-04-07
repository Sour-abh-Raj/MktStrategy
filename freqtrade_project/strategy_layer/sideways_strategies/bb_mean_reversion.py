from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from freqtrade_project.core.indicators import atr, bollinger, rsi
from freqtrade_project.strategy_layer.strategy_templates.base_regime_strategy import BaseRegimeStrategy


@dataclass
class SidewaysBBConfig:
    rsi_oversold: float = 35.0
    rsi_overbought: float = 68.0
    atr_stop_mult: float = 1.8


class SidewaysBBMeanReversionStrategy(BaseRegimeStrategy):
    strategy_id = "sideways_bb_mean_reversion"
    regime_compatibility = "sideways"
    timeframe = "15m"
    stoploss = -0.04
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.02
    minimal_roi = {"0": 0.03, "45": 0.015, "120": 0.005}

    def __init__(self, config: SidewaysBBConfig | None = None) -> None:
        self.config = config or SidewaysBBConfig()

    def evaluate(self, closes: List[float], highs: List[float], lows: List[float]) -> Dict[str, float]:
        if len(closes) < 25:
            return {"enter": 0.0, "exit": 0.0, "atr_stop": 0.0}

        bb = bollinger(closes)
        current = closes[-1]
        lower = bb["lower"][-1]
        mid = bb["mid"][-1]
        upper = bb["upper"][-1]
        r = rsi(closes)[-1]
        a = atr(highs, lows, closes)[-1]

        enter = 1.0 if current <= lower and r <= self.config.rsi_oversold else 0.0
        exit_signal = 1.0 if current >= mid or r >= self.config.rsi_overbought or current >= upper else 0.0
        atr_stop = current - (a * self.config.atr_stop_mult)
        return {"enter": enter, "exit": exit_signal, "atr_stop": atr_stop}
