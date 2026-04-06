from __future__ import annotations

from typing import Dict, List

from freqtrade_project.core.interfaces import MarketState, StressLevel
from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.market_state_classifier import (
    state_hash,
)
from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.strategy_ranking_engine import (
    StrategyRankingEngine,
)
from freqtrade_project.strategy_layer.strategy_library.library import StrategyLibrary


class RegimeStrategyMapper:
    """Maps strategies to market regimes based on their characteristics."""

    # Regime definitions based on market state parameters
    REGIME_DEFINITIONS = {
        "bullish": {
            "trend_required": "bullish",
            "volatility_max": 0.08,
            "momentum_min": "strong",
            "preferred_strategies": ["trend_breakout", "momentum"],
        },
        "bearish": {
            "trend_required": "bearish",
            "volatility_max": 0.08,
            "momentum_min": "strong",
            "preferred_strategies": ["breakdown", "short_bias"],
        },
        "sideways": {
            "trend_required": "neutral",
            "volatility_max": 0.06,
            "momentum_max": "weak",
            "preferred_strategies": ["mean_reversion", "range_trading"],
        },
        "high_volatility": {
            "volatility_min": 0.08,
            "preferred_strategies": ["options_strategies", "volatility_arbitrage"],
        },
        "low_volatility": {
            "volatility_max": 0.03,
            "preferred_strategies": ["carry", "trend_following"],
        },
    }

    def classify_regime(self, market_state) -> str:
        """Classify the current market regime based on state parameters."""
        trend = market_state.trend.value
        volatility = market_state.volatility.value
        momentum = market_state.momentum.value

        # High volatility override
        if volatility == "high":
            return "high_volatility"

        # Low volatility override
        if volatility == "low":
            return "low_volatility"

        # Trend-based classification
        if trend == "bullish" and momentum in ["strong", "weak"]:
            return "bullish"
        elif trend == "bearish" and momentum in ["strong", "weak"]:
            return "bearish"
        elif trend == "neutral" and momentum == "weak":
            return "sideways"

        # Default fallback
        return "sideways"

    def get_regime_compatibility_score(self, strategy_id: str, regime: str) -> float:
        """Score how compatible a strategy is with a given regime."""
        # Extract strategy type from ID
        strategy_type = self._extract_strategy_type(strategy_id)

        regime_prefs = self.REGIME_DEFINITIONS.get(regime, {}).get(
            "preferred_strategies", []
        )

        # Perfect match
        if any(pref in strategy_type.lower() for pref in regime_prefs):
            return 1.0

        # Partial match
        if any(
            word in strategy_type.lower() for word in ["trend", "momentum", "breakout"]
        ):
            if regime in ["bullish", "bearish"]:
                return 0.8

        if "mean_reversion" in strategy_type.lower() and regime == "sideways":
            return 0.9

        # Neutral match
        return 0.5

    def _extract_strategy_type(self, strategy_id: str) -> str:
        """Extract strategy type from strategy ID."""
        # Remove prefixes and suffixes
        clean_id = strategy_id.replace("alpha_", "").replace("_gen_", "_").split("_")[0]
        return clean_id


class StrategySelector:
    def __init__(
        self,
        ranking_engine: StrategyRankingEngine,
        strategy_library: StrategyLibrary | None = None,
    ) -> None:
        self.ranking_engine = ranking_engine
        self.strategy_library = strategy_library or StrategyLibrary()
        self.regime_mapper = RegimeStrategyMapper()

    def select(self, market_state, stress, limit: int = 3) -> List[str]:
        """Select strategies with regime-aware filtering."""
        # Classify current regime
        current_regime = self.regime_mapper.classify_regime(market_state)

        # Get ranked strategies for current market state
        ranked = self.ranking_engine.rank(state_hash(market_state))
        ranked_ids = [sid for sid, _ in ranked]

        # Filter by regime compatibility
        regime_filtered = []
        for sid in ranked_ids:
            compatibility = self.regime_mapper.get_regime_compatibility_score(
                sid, current_regime
            )
            if compatibility >= 0.7:  # Minimum compatibility threshold
                regime_filtered.append((sid, compatibility))

        # Sort by compatibility score
        regime_filtered.sort(key=lambda x: x[1], reverse=True)
        eligible_ids = [sid for sid, _ in regime_filtered]

        # Apply stress-based filtering
        if stress.value == "elevated":
            eligible_ids = [sid for sid in eligible_ids if "mean_reversion" not in sid]
        elif stress.value == "extreme":
            return []

        # Fallback to regime-compatible strategies if none pass all filters
        if not eligible_ids:
            eligible_ids = [
                rec.strategy_id
                for rec in self.strategy_library.for_regime(current_regime)
            ]

        return eligible_ids[:limit]

    def get_regime_performance_map(self) -> Dict[str, Dict[str, float]]:
        """Get performance map of strategies across regimes."""
        # This would be populated from historical backtest data
        # For now, return a mock performance map
        return {
            "bullish": {
                "trend_breakout": 0.85,
                "momentum": 0.75,
                "mean_reversion": 0.45,
            },
            "bearish": {
                "breakdown": 0.80,
                "short_bias": 0.70,
                "trend_breakout": 0.40,
            },
            "sideways": {
                "mean_reversion": 0.90,
                "range_trading": 0.85,
                "trend_breakout": 0.35,
            },
        }
