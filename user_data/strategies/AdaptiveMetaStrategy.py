from __future__ import annotations

from datetime import datetime
from typing import Dict

import pandas as pd

try:
    from freqtrade.strategy import IStrategy
except Exception:  # pragma: no cover
    class IStrategy:  # type: ignore
        timeframe = "15m"

from freqtrade_project.pipeline import AdaptiveTradingSystem, CycleInput


class AdaptiveMetaStrategy(IStrategy):
    """Freqtrade adapter that delegates signal intelligence to AdaptiveTradingSystem."""

    timeframe = "15m"
    can_short = True
    minimal_roi = {"0": 0.03, "30": 0.015, "120": 0.0}
    stoploss = -0.08
    trailing_stop = True
    trailing_stop_positive = 0.015
    trailing_stop_positive_offset = 0.03

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__()
        self.system = AdaptiveTradingSystem()
        self._last_result: Dict[str, object] = {}

    def _to_rows(self, dataframe: pd.DataFrame):
        rows = []
        for _, r in dataframe.tail(200).iterrows():
            ts = r.get("date", datetime.utcnow())
            rows.append(
                {
                    "timestamp": ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts,
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "volume": float(r["volume"]),
                }
            )
        return rows

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        if len(dataframe) < 40:
            dataframe["adaptive_signal"] = 0
            dataframe["adaptive_exit"] = 0
            return dataframe

        cycle = CycleInput(
            pair=metadata.get("pair", "BTC/USDT"),
            timeframe=self.timeframe,
            raw_rows=self._to_rows(dataframe),
            tf_scores={"1d": 0.0, "4h": 0.0, "15m": 0.0},
            stress_metrics={
                "volatility_current": 0.02,
                "volatility_average": 0.02,
                "price_change_5m": 0.0,
                "price_change_15m": 0.0,
                "spread": 0.001,
                "spread_avg": 0.001,
                "volume_ratio": 1.0,
                "portfolio_drawdown": 0.0,
                "api_errors": 0,
            },
            equity=10000,
        )
        result = self.system.run_cycle(cycle)
        self._last_result = result

        has_signal = 1 if result.get("active_strategies") else 0
        dataframe["adaptive_signal"] = 0
        dataframe.loc[dataframe.index[-1], "adaptive_signal"] = has_signal
        dataframe["adaptive_exit"] = 0
        dataframe.loc[dataframe.index[-1], "adaptive_exit"] = 1 if result.get("halt_new_entries") else 0
        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[dataframe["adaptive_signal"] > 0, "enter_long"] = 1
        dataframe.loc[dataframe["adaptive_signal"] > 0, "enter_tag"] = "adaptive_meta"
        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[dataframe["adaptive_exit"] > 0, "exit_long"] = 1
        dataframe.loc[dataframe["adaptive_exit"] > 0, "exit_tag"] = "adaptive_risk"
        return dataframe
