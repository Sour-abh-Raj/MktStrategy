from __future__ import annotations

from typing import List

from freqtrade_project.strategy_layer.strategy_evolution_engine.crossover_engine import CrossoverEngine
from freqtrade_project.strategy_layer.strategy_evolution_engine.fitness_evaluator import FitnessEvaluator, FitnessResult
from freqtrade_project.strategy_layer.strategy_evolution_engine.mutation_engine import MutationEngine
from freqtrade_project.strategy_layer.strategy_evolution_engine.strategy_generator import CandidateStrategy, StrategyGenerator


class EvolutionController:
    def __init__(self) -> None:
        self.generator = StrategyGenerator()
        self.mutation = MutationEngine()
        self.crossover = CrossoverEngine()
        self.fitness = FitnessEvaluator()

    def evolve(self, regime: str, generations: int = 2, population_size: int = 8) -> List[CandidateStrategy]:
        population = self.generator.generate(regime, population_size)
        for gen in range(generations):
            scored: List[FitnessResult] = [
                self.fitness.evaluate(c, sharpe=1.0 + (idx / 10), drawdown=0.1 + (idx / 100), win_rate=0.45 + (idx / 100))
                for idx, c in enumerate(population)
            ]
            scored.sort(key=lambda x: x.score, reverse=True)
            elites = [s.candidate for s in scored[: max(2, population_size // 3)]]
            next_population: List[CandidateStrategy] = elites.copy()
            while len(next_population) < population_size:
                p1 = elites[len(next_population) % len(elites)]
                p2 = elites[(len(next_population) + 1) % len(elites)]
                child = self.crossover.crossover(p1, p2, child_id=f"{regime}_g{gen}_{len(next_population)}")
                next_population.append(self.mutation.mutate(child))
            population = next_population
        return population
