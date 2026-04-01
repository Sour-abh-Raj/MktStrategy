from __future__ import annotations

from typing import List

from freqtrade_project.core.interfaces import MarketState, StressLevel
from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.market_state_classifier import state_hash
from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.strategy_ranking_engine import StrategyRankingEngine
from freqtrade_project.strategy_layer.strategy_library.library import StrategyLibrary


class StrategySelector:
    def __init__(self, ranking_engine: StrategyRankingEngine, strategy_library: StrategyLibrary | None = None) -> None:
        self.ranking_engine = ranking_engine
        self.strategy_library = strategy_library or StrategyLibrary()

    def select(self, market_state: MarketState, stress: StressLevel, limit: int = 3) -> List[str]:
        ranked = self.ranking_engine.rank(state_hash(market_state))
        ranked_ids = [sid for sid, _ in ranked]

        eligible_by_regime = {rec.strategy_id for rec in self.strategy_library.for_regime(market_state.regime)}
        if eligible_by_regime:
            ranked_ids = [sid for sid in ranked_ids if sid in eligible_by_regime]

        if stress == StressLevel.ELEVATED:
            ranked_ids = [sid for sid in ranked_ids if "mean_reversion" not in sid]
        if stress == StressLevel.EXTREME:
            return []

        if not ranked_ids:
            fallback = [rec.strategy_id for rec in self.strategy_library.for_regime(market_state.regime)]
            return fallback[:limit]

        return ranked_ids[:limit]
