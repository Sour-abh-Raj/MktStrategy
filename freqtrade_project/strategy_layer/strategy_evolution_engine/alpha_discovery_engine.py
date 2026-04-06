from __future__ import annotations

import random
from typing import List, Optional

from freqtrade_project.strategy_layer.strategy_evolution_engine.strategy_generator import (
    CandidateStrategy,
)


class AlphaDiscoveryEngine:
    """Basic alpha discovery engine."""

    def __init__(self, random_seed: Optional[int] = None) -> None:
        self.random_seed = random_seed
        if random_seed is not None:
            random.seed(random_seed)

    def generate_strategy_population(
        self, population_size: int = 100, regime: str = "universal"
    ) -> List[CandidateStrategy]:
        """Generate basic strategies."""
        population = []
        for i in range(population_size):
            strategy_id = f"alpha_{regime}_{i:03d}"
            strategy_params = {
                "ema_fast": random.randint(5, 20),
                "ema_slow": random.randint(21, 50),
                "rsi_period": random.randint(7, 21),
                "stop_loss": round(random.uniform(0.02, 0.08), 3),
            }
            population.append(
                CandidateStrategy(
                    strategy_id=strategy_id, regime=regime, params=strategy_params
                )
            )
        return population

    def generate_targeted_strategies(
        self, target_regime: str, num_strategies: int = 50
    ) -> List[CandidateStrategy]:
        """Generate targeted strategies."""
        return self.generate_strategy_population(num_strategies, target_regime)
