"""
Market Regime Service - Single source of truth for regime classification.

This module provides a unified interface for market regime detection,
consolidating logic from both intelligence_layer and decision_layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Protocol, List, Optional
import numpy as np


class Trend(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class VolatilityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MomentumState(str, Enum):
    STRONG = "strong"
    WEAK = "weak"
    REVERSAL = "reversal"


class LiquidityState(str, Enum):
    HIGH = "high"
    LOW = "low"


class MarketRegime(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass(frozen=True)
class MarketState:
    trend: Trend
    volatility: VolatilityLevel
    momentum: MomentumState
    liquidity: LiquidityState
    regime: str
    context_score: float


class MarketRegimeService(Protocol):
    """Protocol for regime classification services."""
    
    def classify(self, indicators: Dict[str, float]) -> MarketState:
        """Classify market state from indicators."""
        ...


class RegimeClassifier:
    """Unified regime classifier using multiple signal sources."""
    
    # Thresholds for regime classification
    VOLATILITY_HIGH_THRESHOLD = 0.02  # 2% daily
    VOLATILITY_LOW_THRESHOLD = 0.005   # 0.5% daily
    
    MOMENTUM_STRONG_THRESHOLD = 0.5    # RSI > 50
    MOMENTUM_WEAK_THRESHOLD = -0.5
    
    TREND_BULLISH_THRESHOLD = 0.3      # MA slope
    TREND_BEARISH_THRESHOLD = -0.3
    
    def __init__(self) -> None:
        self._last_state: Optional[MarketState] = None
    
    def classify(
        self,
        trend: Trend,
        volatility: VolatilityLevel,
        momentum: MomentumState,
        liquidity: LiquidityState,
        context_score: float = 0.5,
    ) -> MarketState:
        """Create MarketState from individual components."""
        # Determine composite regime
        regime = self._determine_regime(trend, volatility)
        
        state = MarketState(
            trend=trend,
            volatility=volatility,
            momentum=momentum,
            liquidity=liquidity,
            regime=regime.value,
            context_score=context_score,
        )
        self._last_state = state
        return state
    
    def classify_from_indicators(self, indicators: Dict[str, float]) -> MarketState:
        """Classify market state directly from indicator dictionary."""
        trend = self._classify_trend(indicators)
        volatility = self._classify_volatility(indicators)
        momentum = self._classify_momentum(indicators)
        liquidity = self._classify_liquidity(indicators)
        
        context_score = self._compute_context_score(indicators)
        
        return self.classify(trend, volatility, momentum, liquidity, context_score)
    
    def _determine_regime(self, trend: Trend, volatility: VolatilityLevel) -> MarketRegime:
        """Determine composite market regime from components."""
        if volatility == VolatilityLevel.HIGH:
            return MarketRegime.HIGH_VOLATILITY
        elif volatility == VolatilityLevel.LOW:
            return MarketRegime.LOW_VOLATILITY
        elif trend == Trend.BULLISH:
            return MarketRegime.BULLISH
        elif trend == Trend.BEARISH:
            return MarketRegime.BEARISH
        else:
            return MarketRegime.SIDEWAYS
    
    def _classify_trend(self, indicators: Dict[str, float]) -> Trend:
        """Classify trend direction from indicators."""
        ma_slope = indicators.get("ma_slope", 0.0)
        macd_hist = indicators.get("macd_hist", 0.0)
        
        # Combined signal
        combined = (ma_slope / 10.0) + (macd_hist * 100)
        
        if combined > self.TREND_BULLISH_THRESHOLD:
            return Trend.BULLISH
        elif combined < self.TREND_BEARISH_THRESHOLD:
            return Trend.BEARISH
        return Trend.NEUTRAL
    
    def _classify_volatility(self, indicators: Dict[str, float]) -> VolatilityLevel:
        """Classify volatility regime."""
        atr_ratio = indicators.get("atr_ratio", 1.0)
        bb_width = indicators.get("bb_width", 0.02)
        
        if atr_ratio > 2.0 or bb_width > 0.04:
            return VolatilityLevel.HIGH
        elif atr_ratio < 0.5 or bb_width < 0.01:
            return VolatilityLevel.LOW
        return VolatilityLevel.MEDIUM
    
    def _classify_momentum(self, indicators: Dict[str, float]) -> MomentumState:
        """Classify momentum state."""
        rsi = indicators.get("rsi", 50.0)
        stoch_k = indicators.get("stoch_k", 50.0)
        
        if rsi > 60 and stoch_k > 60:
            return MomentumState.STRONG
        elif rsi < 40 and stoch_k < 40:
            return MomentumState.REVERSAL  # Oversold - potential reversal
        return MomentumState.WEAK
    
    def _classify_liquidity(self, indicators: Dict[str, float]) -> LiquidityState:
        """Classify liquidity state."""
        volume_ratio = indicators.get("volume_ratio", 1.0)
        
        if volume_ratio >= 0.8 and volume_ratio <= 1.5:
            return LiquidityState.HIGH
        return LiquidityState.LOW
    
    def _compute_context_score(self, indicators: Dict[str, float]) -> float:
        """Compute overall market context score (0-1)."""
        scores = []
        
        # Trend confidence
        ma_slope = abs(indicators.get("ma_slope", 0.0))
        scores.append(min(ma_slope / 0.5, 1.0))
        
        # Momentum confidence
        rsi = indicators.get("rsi", 50.0)
        rsi_conf = abs(rsi - 50) / 50
        scores.append(rsi_conf)
        
        # Volatility regime confidence
        atr_ratio = indicators.get("atr_ratio", 1.0)
        if 0.5 <= atr_ratio <= 2.0:
            scores.append(1.0 - abs(atr_ratio - 1.0))
        else:
            scores.append(0.5)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def get_last_state(self) -> Optional[MarketState]:
        """Get the last classified state."""
        return self._last_state


# Singleton instance for system-wide use
_default_classifier: Optional[RegimeClassifier] = None


def get_regime_classifier() -> RegimeClassifier:
    """Get the default regime classifier instance."""
    global _default_classifier
    if _default_classifier is None:
        _default_classifier = RegimeClassifier()
    return _default_classifier


def classify_market_state(indicators: Dict[str, float]) -> MarketState:
    """Convenience function to classify market state from indicators."""
    classifier = get_regime_classifier()
    return classifier.classify_from_indicators(indicators)
