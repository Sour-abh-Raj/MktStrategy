from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class StrategyStateMetrics:
    trade_count: int = 0
    sharpe: float = 0.0
    win_rate: float = 0.0
    avg_return: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0


class RegimePerformanceDatabase:
    """In-memory metrics store keyed by (strategy_id, market_state_hash)."""

    def __init__(self) -> None:
        self._store: Dict[Tuple[str, str], StrategyStateMetrics] = defaultdict(StrategyStateMetrics)

    def upsert(self, strategy_id: str, state_hash: str, metrics: StrategyStateMetrics) -> None:
        self._store[(strategy_id, state_hash)] = metrics

    def get(self, strategy_id: str, state_hash: str) -> StrategyStateMetrics:
        return self._store[(strategy_id, state_hash)]

    def all_for_state(self, state_hash: str) -> Dict[str, StrategyStateMetrics]:
        return {s: m for (s, h), m in self._store.items() if h == state_hash}
