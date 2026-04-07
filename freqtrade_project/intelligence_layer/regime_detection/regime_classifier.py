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
    ma_slope_bull: float = 0.001       # require a meaningful positive slope
    ma_slope_bear: float = -0.001      # require a meaningful negative slope
    vol_high: float = 0.04
    vol_low: float = 0.015
    momentum_strong: float = 0.6
    momentum_reversal: float = -0.5
    liquidity_high: float = 1.1


class RegimeClassifier:
    """Deterministic regime + market-state classifier for backtests and live routing."""

    def __init__(self, thresholds: RegimeThresholds | None = None) -> None:
        self.t = thresholds or RegimeThresholds()

    @classmethod
    def from_yaml(cls, path: str) -> "RegimeClassifier":
        """Load thresholds from a YAML config file."""
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
            t = RegimeThresholds(**{k: float(v) for k, v in raw.items() if hasattr(RegimeThresholds, k)})
            return cls(t)
        except Exception:
            return cls()

    def classify(self, indicators: Dict[str, float]) -> MarketState:
        ma_slope = indicators.get("ma_slope", 0.0)
        adx = indicators.get("adx", 0.0)
        rsi_val = indicators.get("rsi", 50.0)
        macd = indicators.get("macd_hist", 0.0)
        rv = indicators.get("realized_volatility", 0.02)
        momentum = indicators.get("momentum_score", 0.0)
        volume_ratio = indicators.get("volume_ratio", 1.0)

        # --- Trend / Regime ---
        if ma_slope > self.t.ma_slope_bull and adx >= self.t.adx_trend and macd >= 0 and rsi_val >= 52:
            trend = Trend.BULLISH
            regime = "bullish"
        elif ma_slope < self.t.ma_slope_bear and adx >= self.t.adx_trend and macd <= 0 and rsi_val <= 48:
            trend = Trend.BEARISH
            regime = "bearish"
        else:
            trend = Trend.NEUTRAL
            regime = "sideways"

        # --- Volatility ---
        if rv >= self.t.vol_high:
            volatility = VolatilityLevel.HIGH
        elif rv <= self.t.vol_low:
            volatility = VolatilityLevel.LOW
        else:
            volatility = VolatilityLevel.MEDIUM

        # --- Momentum ---
        if momentum >= self.t.momentum_strong:
            m_state = MomentumState.STRONG
        elif momentum <= self.t.momentum_reversal:
            m_state = MomentumState.REVERSAL
        else:
            m_state = MomentumState.WEAK

        # --- Liquidity ---
        liquidity = LiquidityState.HIGH if volume_ratio >= self.t.liquidity_high else LiquidityState.LOW

        # --- Context score — all terms clamped to [0, 1] before weighting ---
        adx_term = min(adx / 100.0, 1.0) * 0.35
        slope_term = max(min(ma_slope, 1.0), -1.0) * 0.25
        # Clamp realized vol contribution: rv=0 → 0.2, rv≥1 → 0.0 (never negative)
        rv_term = max(1.0 - min(rv, 1.0), 0.0) * 0.20
        vol_ratio_term = min(volume_ratio, 2.0) / 2.0 * 0.20
        context_score = adx_term + slope_term + rv_term + vol_ratio_term

        return MarketState(
            trend=trend,
            volatility=volatility,
            momentum=m_state,
            liquidity=liquidity,
            regime=regime,
            context_score=round(context_score, 4),
        )
