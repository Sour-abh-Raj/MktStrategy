from __future__ import annotations

import random

from freqtrade_project.strategy_layer.strategy_evolution_engine.strategy_generator import CandidateStrategy


class MutationEngine:
    def mutate(self, candidate: CandidateStrategy, mutation_rate: float = 0.2) -> CandidateStrategy:
        params = dict(candidate.params)
        for key, value in params.items():
            if random.random() < mutation_rate:
                jitter = random.uniform(-0.2, 0.2)
                params[key] = max(1, value * (1 + jitter))
        return CandidateStrategy(strategy_id=f"{candidate.strategy_id}_m", regime=candidate.regime, params=params)
