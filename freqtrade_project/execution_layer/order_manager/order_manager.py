from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OrderRequest:
    strategy_id: str
    pair: str
    side: str
    stake: float


class OrderManager:
    def create_order(self, strategy_id: str, pair: str, side: str, stake: float) -> OrderRequest:
        return OrderRequest(strategy_id=strategy_id, pair=pair, side=side, stake=round(stake, 2))
