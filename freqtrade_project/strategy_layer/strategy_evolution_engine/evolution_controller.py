from __future__ import annotations

import random
from typing import List, Optional

from freqtrade_project.strategy_layer.strategy_evolution_engine.alpha_discovery_engine import (
    AlphaDiscoveryEngine,
)
from freqtrade_project.strategy_layer.strategy_evolution_engine.crossover_engine import (
    CrossoverEngine,
)
from freqtrade_project.strategy_layer.strategy_evolution_engine.fitness_evaluator import (
    FitnessEvaluator,
    FitnessResult,
)
from freqtrade_project.strategy_layer.strategy_evolution_engine.mutation_engine import (
    MutationEngine,
)
from freqtrade_project.strategy_layer.strategy_evolution_engine.strategy_generator import (
    CandidateStrategy,
)


class EvolutionController:
    """Runs a simple (µ + λ) genetic algorithm over CandidateStrategies.

    Parameters
    ----------
    random_seed : int | None
        Pass an integer for fully reproducible evolution runs.
        None (default) uses the system entropy source.
    """

    def __init__(self, random_seed: Optional[int] = None) -> None:
        self.alpha_discovery = AlphaDiscoveryEngine(random_seed)
        self.generator = self.alpha_discovery  # Use alpha discovery for generation
        self.mutation = MutationEngine()
        self.crossover = CrossoverEngine()
        self.fitness = FitnessEvaluator(ranking_method="risk_adjusted")
        self._seed = random_seed

    def evolve(
        self,
        regime: str,
        generations: int = 5,
        population_size: int = 12,
    ) -> List[CandidateStrategy]:
        """Evolve a population of strategies for `regime` over `generations`.

        Fitness is evaluated via FitnessEvaluator; in production this should
        be connected to real backtest metrics.  Here simulated metrics provide
        a useful smoke-test baseline.
        """
        population = self.alpha_discovery.generate_strategy_population(
            population_size, regime
        )

        for gen in range(generations):
            scored: List[FitnessResult] = [
                self.fitness.evaluate(
                    c,
                    sharpe=1.0 + (idx / 10),
                    drawdown=max(0.05, 0.15 - (idx / 100)),
                    win_rate=min(0.45 + (idx / 100), 0.75),
                )
                for idx, c in enumerate(population)
            ]
            scored.sort(key=lambda x: x.score, reverse=True)

            # Elite fraction — at least 2 survivors
            n_elites = max(2, population_size // 4)
            elites = [s.candidate for s in scored[:n_elites]]
            next_population: List[CandidateStrategy] = list(elites)

            while len(next_population) < population_size:
                idx = len(next_population)
                p1 = elites[idx % len(elites)]
                p2 = elites[(idx + 1) % len(elites)]
                child_id = f"{regime}_g{gen}_{idx}"
                child = self.crossover.crossover(p1, p2, child_id=child_id)
                next_population.append(self.mutation.mutate(child))

            population = next_population

        return population

    def discover_alpha(
        self, target_regime: str = "universal", num_strategies: int = 1000
    ) -> List[CandidateStrategy]:
        """Discover alpha strategies using advanced generation techniques.

        Generates a large population of diverse strategies optimized for alpha discovery.
        """
        return self.alpha_discovery.generate_strategy_population(
            num_strategies, target_regime
        )

    def discover_regime_specific_alpha(
        self, regime: str, num_strategies: int = 200
    ) -> List[CandidateStrategy]:
        """Discover strategies specifically optimized for a market regime."""
        return self.alpha_discovery.generate_targeted_strategies(regime, num_strategies)
