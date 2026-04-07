from __future__ import annotations

from dataclasses import dataclass
from typing import List

from freqtrade_project.core.interfaces import MarketState, StressLevel
from freqtrade_project.decision_layer.strategy_selector.selector import StrategySelector
from freqtrade_project.strategy_layer.strategy_library.library import StrategyLibrary


@dataclass
class StrategyActivationPlan:
    active_strategies: List[str]
    regime: str
    stress_level: StressLevel


class MetaStrategyController:
    """Selects and activates the best-fit strategies for the current market state."""

    def __init__(self, selector: StrategySelector, strategy_library: StrategyLibrary | None = None) -> None:
        self.selector = selector
        # Keep a direct reference to the library for regime-compatibility filtering
        self.strategy_library = strategy_library or selector.strategy_library

    def plan(self, state: MarketState, stress: StressLevel) -> StrategyActivationPlan:
        candidates = self.selector.select(state, stress)

        # Build a set of strategy_ids whose declared regime_compatibility matches
        # the current market regime. The library records carry this information.
        compatible_ids = {
            rec.strategy_id
            for rec in self.strategy_library.for_regime(state.regime)
        }

        if compatible_ids:
            # Prefer regime-compatible strategies first; fall back to all candidates
            filtered = [s for s in candidates if s in compatible_ids]
        else:
            filtered = []

        active = filtered if filtered else candidates
        return StrategyActivationPlan(
            active_strategies=active,
            regime=state.regime,
            stress_level=stress,
        )
