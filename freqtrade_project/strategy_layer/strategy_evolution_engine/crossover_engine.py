from __future__ import annotations

from freqtrade_project.strategy_layer.strategy_evolution_engine.strategy_generator import CandidateStrategy


class CrossoverEngine:
    def crossover(self, left: CandidateStrategy, right: CandidateStrategy, child_id: str) -> CandidateStrategy:
        params = {}
        for key in left.params.keys():
            params[key] = left.params[key] if hash(key + child_id) % 2 == 0 else right.params[key]
        return CandidateStrategy(strategy_id=child_id, regime=left.regime, params=params)
