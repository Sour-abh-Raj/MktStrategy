from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class BinanceDataCollector:
    """Adapter-friendly collector for Binance OHLCV rows.

    In production this class should use ccxt/freqtrade data handlers.
    Here it normalizes incoming iterable records into Candle objects.
    """

    def normalize(self, rows: Iterable[dict]) -> List[Candle]:
        candles: List[Candle] = []
        for row in rows:
            candles.append(
                Candle(
                    timestamp=row["timestamp"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )
        return candles
