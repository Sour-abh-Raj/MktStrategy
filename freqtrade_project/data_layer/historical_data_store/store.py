from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from freqtrade_project.data_layer.data_collector.binance_collector import Candle


class HistoricalDataStore:
    def __init__(self, base_path: str = "freqtrade_project/data") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, pair: str, timeframe: str) -> Path:
        filename = f"{pair.replace('/', '_')}_{timeframe}.jsonl"
        return self.base_path / filename

    def save(self, pair: str, timeframe: str, candles: Iterable[Candle]) -> Path:
        path = self._path(pair, timeframe)
        with path.open("w", encoding="utf-8") as fh:
            for candle in candles:
                payload = asdict(candle)
                payload["timestamp"] = candle.timestamp.isoformat()
                fh.write(json.dumps(payload) + "\n")
        return path

    def load(self, pair: str, timeframe: str) -> List[Candle]:
        path = self._path(pair, timeframe)
        if not path.exists():
            return []
        data: List[Candle] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                raw = json.loads(line)
                data.append(
                    Candle(
                        timestamp=datetime.fromisoformat(raw["timestamp"]),
                        open=raw["open"],
                        high=raw["high"],
                        low=raw["low"],
                        close=raw["close"],
                        volume=raw["volume"],
                    )
                )
        return data
