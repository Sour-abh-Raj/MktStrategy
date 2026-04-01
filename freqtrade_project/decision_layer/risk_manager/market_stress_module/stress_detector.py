from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class StressSignals:
    volatility_shock: bool
    rapid_price_move: bool
    liquidity_shock: bool
    volume_surge: bool


class StressDetector:
    def detect(self, metrics: Dict[str, float]) -> StressSignals:
        return StressSignals(
            volatility_shock=metrics.get("volatility_current", 0) > 2 * metrics.get("volatility_average", 1),
            rapid_price_move=(abs(metrics.get("price_change_5m", 0)) > 0.05)
            or (abs(metrics.get("price_change_15m", 0)) > 0.08),
            liquidity_shock=metrics.get("spread", 0.0) > metrics.get("spread_avg", 0.0) * 2
            or metrics.get("volume_ratio", 1.0) < 0.5,
            volume_surge=metrics.get("volume_ratio", 1.0) > 3.0,
        )
