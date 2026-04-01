from __future__ import annotations

from typing import Dict, Iterable


class PortfolioAllocationEngine:
    def allocate(self, strategies: Iterable[str], equity: float, max_position_size: float) -> Dict[str, float]:
        strategies = list(strategies)
        if not strategies:
            return {}
        per = min(equity / len(strategies), equity * max_position_size)
        return {s: round(per, 2) for s in strategies}
