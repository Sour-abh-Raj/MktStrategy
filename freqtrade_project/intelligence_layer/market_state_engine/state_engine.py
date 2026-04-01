from __future__ import annotations

from typing import Dict

from freqtrade_project.core.interfaces import MarketState
from freqtrade_project.intelligence_layer.multi_timeframe_analysis.mtf_engine import MultiTimeframeAnalysisEngine
from freqtrade_project.intelligence_layer.regime_detection.regime_classifier import RegimeClassifier


class MarketStateEngine:
    def __init__(self) -> None:
        self.regime = RegimeClassifier()
        self.mtf = MultiTimeframeAnalysisEngine()

    def evaluate(self, indicators: Dict[str, float], tf_scores: Dict[str, float]) -> MarketState:
        state = self.regime.classify(indicators)
        merged_score = (state.context_score * 0.6) + (self.mtf.compute_context_score(tf_scores) * 0.4)
        return MarketState(
            trend=state.trend,
            volatility=state.volatility,
            momentum=state.momentum,
            liquidity=state.liquidity,
            regime=state.regime,
            context_score=round(merged_score, 4),
        )
