from __future__ import annotations

from typing import Dict, Iterable

from freqtrade_project.data_layer.data_collector.binance_collector import BinanceDataCollector
from freqtrade_project.data_layer.feature_engineering.engine import FeatureEngineeringEngine
from freqtrade_project.data_layer.historical_data_store.store import HistoricalDataStore


class DatasetManager:
    def __init__(self) -> None:
        self.collector = BinanceDataCollector()
        self.store = HistoricalDataStore()
        self.features = FeatureEngineeringEngine()

    def ingest(self, pair: str, timeframe: str, rows: Iterable[dict]) -> Dict[str, float]:
        candles = self.collector.normalize(rows)
        self.store.save(pair, timeframe, candles)
        return self.features.build(candles)
