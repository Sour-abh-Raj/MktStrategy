from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from freqtrade_project.core.interfaces import (
    LiquidityState,
    MarketState,
    MomentumState,
    Trend,
    VolatilityLevel,
)


@dataclass
class RegimeThresholds:
    adx_trend: float = 22.0
    ma_slope_bull: float = 0.0
    ma_slope_bear: float = 0.0
    vol_high: float = 0.04
    vol_low: float = 0.015
    momentum_strong: float = 0.6
    momentum_reversal: float = -0.5
    liquidity_high: float = 1.1


class RegimeClassifier:
    """Deterministic regime + market-state classifier for backtests and live routing."""

    def __init__(self, thresholds: RegimeThresholds | None = None) -> None:
        self.t = thresholds or RegimeThresholds()

    def classify(self, indicators: Dict[str, float]) -> MarketState:
        ma_slope = indicators.get("ma_slope", 0.0)
        adx = indicators.get("adx", 0.0)
        rsi = indicators.get("rsi", 50.0)
        macd = indicators.get("macd_hist", 0.0)
        rv = indicators.get("realized_volatility", 0.02)
        momentum = indicators.get("momentum_score", 0.0)
        volume_ratio = indicators.get("volume_ratio", 1.0)

        if ma_slope > self.t.ma_slope_bull and adx >= self.t.adx_trend and macd >= 0 and rsi >= 52:
            trend = Trend.BULLISH
            regime = "bullish"
        elif ma_slope < self.t.ma_slope_bear and adx >= self.t.adx_trend and macd <= 0 and rsi <= 48:
            trend = Trend.BEARISH
            regime = "bearish"
        else:
            trend = Trend.NEUTRAL
            regime = "sideways"

        if rv >= self.t.vol_high:
            volatility = VolatilityLevel.HIGH
        elif rv <= self.t.vol_low:
            volatility = VolatilityLevel.LOW
        else:
            volatility = VolatilityLevel.MEDIUM

        if momentum >= self.t.momentum_strong:
            m_state = MomentumState.STRONG
        elif momentum <= self.t.momentum_reversal:
            m_state = MomentumState.REVERSAL
        else:
            m_state = MomentumState.WEAK

        liquidity = LiquidityState.HIGH if volume_ratio >= self.t.liquidity_high else LiquidityState.LOW

        context_score = (adx / 100.0) * 0.35 + max(min(ma_slope, 1.0), -1.0) * 0.25 + (1 - rv) * 0.2 + volume_ratio * 0.2
        return MarketState(
            trend=trend,
            volatility=volatility,
            momentum=m_state,
            liquidity=liquidity,
            regime=regime,
            context_score=round(context_score, 4),
        )
