from __future__ import annotations

import hashlib

from freqtrade_project.strategy_layer.strategy_evolution_engine.strategy_generator import (
    CandidateStrategy,
)


class CrossoverEngine:
    """Basic crossover engine for strategy evolution."""

    def crossover(
        self,
        left: CandidateStrategy,
        right: CandidateStrategy,
        child_id: str,
    ) -> CandidateStrategy:
        """Basic crossover of strategy parameters."""
        params = {}
        for key in left.params.keys():
            # Simple 50/50 crossover
            digest = int(hashlib.md5(f"{key}{child_id}".encode()).hexdigest(), 16)
            params[key] = (
                left.params[key]
                if digest % 2 == 0
                else right.params.get(key, left.params[key])
            )

        # Choose regime deterministically
        regime_digest = int(hashlib.md5(f"regime_{child_id}".encode()).hexdigest(), 16)
        child_regime = left.regime if regime_digest % 100 < 60 else right.regime

        return CandidateStrategy(
            strategy_id=child_id,
            regime=child_regime,
            params=params,
        )
