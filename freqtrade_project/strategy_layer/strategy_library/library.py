from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class StrategyRecord:
    strategy_id: str
    regime: str
    parameters: Dict[str, float]
    sharpe: float = 0.0
    max_drawdown: float = 1.0
    win_rate: float = 0.0


@dataclass
class StrategyLibrary:
    min_sharpe: float = 0.8
    max_drawdown: float = 0.2
    records: List[StrategyRecord] = field(default_factory=list)

    def register(self, record: StrategyRecord) -> bool:
        if record.sharpe < self.min_sharpe:
            return False
        if record.max_drawdown > self.max_drawdown:
            return False
        self.records.append(record)
        return True

    def for_regime(self, regime: str) -> List[StrategyRecord]:
        return [r for r in self.records if r.regime == regime]
