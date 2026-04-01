from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BinanceGatewayConfig:
    stake_currency: str = "USDT"
    exchange_name: str = "binance"


class BinanceExchangeGateway:
    def __init__(self, config: BinanceGatewayConfig | None = None) -> None:
        self.config = config or BinanceGatewayConfig()

    def execute(self, allocations):
        return {"status": "paper", "orders": allocations, "exchange": self.config.exchange_name}
