from __future__ import annotations

from dataclasses import dataclass

from freqtrade_project.strategy_layer.strategy_evolution_engine.strategy_generator import CandidateStrategy


@dataclass
class FitnessResult:
    candidate: CandidateStrategy
    score: float


class FitnessEvaluator:
    def evaluate(self, candidate: CandidateStrategy, sharpe: float, drawdown: float, win_rate: float) -> FitnessResult:
        score = 0.5 * sharpe - 0.3 * drawdown + 0.2 * win_rate
        return FitnessResult(candidate=candidate, score=round(score, 4))
