from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CandidateStrategy:
    strategy_id: str
    regime: str
    params: Dict[str, float]


class StrategyGenerator:
    def generate(self, regime: str, population_size: int = 10) -> List[CandidateStrategy]:
        population: List[CandidateStrategy] = []
        for i in range(population_size):
            population.append(
                CandidateStrategy(
                    strategy_id=f"{regime}_gen_{i}",
                    regime=regime,
                    params={
                        "ema_fast": random.randint(5, 20),
                        "ema_slow": random.randint(21, 80),
                        "rsi_entry": random.randint(20, 50),
                        "stoploss": round(random.uniform(0.02, 0.10), 3),
                    },
                )
            )
        return population
