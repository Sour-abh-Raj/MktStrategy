from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from freqtrade_project.pipeline import AdaptiveTradingSystem, CycleInput


def build_rows(seed: float = 100.0, n: int = 96):
    out = []
    p = seed
    start = datetime(2026, 1, 1)
    for i in range(n):
        p *= 1 + (0.001 if i % 5 else -0.0002)
        out.append(
            {
                "timestamp": start + timedelta(minutes=15 * i),
                "open": p * 0.999,
                "high": p * 1.002,
                "low": p * 0.998,
                "close": p,
                "volume": 1000 + i,
            }
        )
    return out


def main():
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(filename="logs/runtime_events.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    system = AdaptiveTradingSystem()
    previous_regime = None

    for day in range(30):
        result = system.run_cycle(
            CycleInput(
                pair="BTC/USDT",
                timeframe="15m",
                raw_rows=build_rows(seed=100 + day),
                tf_scores={"1d": 0.2, "4h": 0.1, "15m": 0.05},
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
        )

        state = result["market_state"]
        if previous_regime != state.regime:
            logging.info("regime_change %s", json.dumps({"from": previous_regime, "to": state.regime}))
            previous_regime = state.regime

        logging.info(
            "strategy_signal %s",
            json.dumps({"active_strategies": result["active_strategies"], "allocations": result["allocations"]}),
        )
        logging.info(
            "risk_event %s",
            json.dumps(
                {
                    "stress": result["stress"],
                    "halt_new_entries": result["halt_new_entries"],
                    "emergency_pause": result["emergency"].pause_system,
                }
            ),
        )
        logging.info("trade_execution %s", json.dumps({"orders": len(result["execution"])}))


if __name__ == "__main__":
    main()
