from __future__ import annotations

from typing import Dict


class AIFeatureBuilder:
    def build(self, indicators: Dict[str, float]) -> Dict[str, float]:
        ma_gap = indicators.get("ma_fast", 0.0) - indicators.get("ma_slow", 0.0)
        return {
            "rsi": indicators.get("rsi", 50.0),
            "macd_hist": indicators.get("macd_hist", 0.0),
            "ma_gap": ma_gap,
            "volume_ratio": indicators.get("volume_ratio", 1.0),
            "volatility": indicators.get("realized_volatility", 0.02),
            "momentum_score": indicators.get("momentum_score", 0.0),
        }
