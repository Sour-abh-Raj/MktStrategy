from __future__ import annotations

from dataclasses import dataclass
from typing import List

from freqtrade_project.core.interfaces import MarketState, StressLevel
from freqtrade_project.decision_layer.strategy_selector.selector import StrategySelector


@dataclass
class StrategyActivationPlan:
    active_strategies: List[str]
    regime: str
    stress_level: StressLevel


class MetaStrategyController:
    def __init__(self, selector: StrategySelector) -> None:
        self.selector = selector

    def plan(self, state: MarketState, stress: StressLevel) -> StrategyActivationPlan:
        candidates = self.selector.select(state, stress)
        filtered = [s for s in candidates if state.regime in s or state.regime == "sideways"]
        return StrategyActivationPlan(active_strategies=filtered or candidates, regime=state.regime, stress_level=stress)
