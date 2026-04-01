from __future__ import annotations

from typing import Dict, List

from freqtrade_project.execution_layer.exchange_interface.binance_gateway import BinanceExchangeGateway
from freqtrade_project.execution_layer.order_manager.order_manager import OrderManager


class TradeExecutor:
    def __init__(self) -> None:
        self.orders = OrderManager()
        self.gateway = BinanceExchangeGateway()

    def execute_allocations(self, pair: str, allocations: Dict[str, float], side: str = "long") -> List[dict]:
        requests = [self.orders.create_order(strategy_id=sid, pair=pair, side=side, stake=stake) for sid, stake in allocations.items()]
        return [self.gateway.execute({"strategy_id": r.strategy_id, "pair": r.pair, "side": r.side, "stake": r.stake}) for r in requests]
