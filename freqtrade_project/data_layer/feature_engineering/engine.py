from __future__ import annotations

from statistics import mean, pstdev
from typing import Dict, List

from freqtrade_project.data_layer.data_collector.binance_collector import Candle


class FeatureEngineeringEngine:
    def build(self, candles: List[Candle], lookback: int = 20) -> Dict[str, float]:
        if len(candles) < max(lookback, 3):
            return {}

        closes = [c.close for c in candles[-lookback:]]
        highs = [c.high for c in candles[-lookback:]]
        lows = [c.low for c in candles[-lookback:]]
        volumes = [c.volume for c in candles[-lookback:]]

        returns = [(closes[i] / closes[i - 1]) - 1 for i in range(1, len(closes))]
        ma_fast = mean(closes[-5:])
        ma_slow = mean(closes)
        ma_slope = (ma_fast - ma_slow) / max(ma_slow, 1e-9)

        tr = [max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])) for i in range(1, len(closes))]
        atr = mean(tr[-14:]) if len(tr) >= 14 else mean(tr)

        return {
            "close": closes[-1],
            "ma_fast": ma_fast,
            "ma_slow": ma_slow,
            "ma_slope": ma_slope,
            "realized_volatility": pstdev(returns) if len(returns) > 1 else 0.0,
            "momentum_score": (closes[-1] / closes[0]) - 1,
            "volume_ratio": volumes[-1] / max(mean(volumes), 1e-9),
            "atr": atr,
            "price_change_5m": returns[-1] if returns else 0.0,
            "price_change_15m": sum(returns[-3:]) if len(returns) >= 3 else 0.0,
        }
