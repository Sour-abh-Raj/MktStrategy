from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from freqtrade_project.backtesting_layer.backtest_runner.runner import BacktestRunner
from freqtrade_project.execution_layer.paper_validation.paper_trading_pipeline import PaperTradingValidationPipeline


def sample_day_rows(seed_price: float = 100.0, candles: int = 96):
    rows = []
    price = seed_price
    for i in range(candles):
        drift = 0.0005 if i % 7 else -0.0003
        price *= 1 + drift
        rows.append(
            {
                "timestamp": datetime(2026, 1, 1) + timedelta(minutes=15 * i),
                "open": price * 0.999,
                "high": price * 1.002,
                "low": price * 0.998,
                "close": price,
                "volume": 1000 + i,
            }
        )
    return rows


def run_pytest():
    proc = subprocess.run(["pytest", "-q"], capture_output=True, text=True)
    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def run_freqtrade_backtest():
    cmd = [
        "freqtrade",
        "backtesting",
        "--strategy",
        "AdaptiveMetaStrategy",
        "--strategy-path",
        "user_data/strategies",
        "--timerange",
        "20240101-20241231",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return {"command": cmd, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    except FileNotFoundError as exc:
        return {"command": cmd, "returncode": 127, "stdout": "", "stderr": str(exc)}


def run_internal_backtest():
    returns = [0.01, -0.006, 0.004, 0.009, -0.003, 0.002, 0.007, -0.002]
    regime_returns = {
        "bullish": [0.012, 0.008, 0.005],
        "bearish": [-0.004, 0.003],
        "sideways": [0.002, -0.001, 0.001],
    }
    report = BacktestRunner().evaluate(returns, regime_returns)
    return {
        "total_return": report.total_return,
        "sharpe": report.metrics.sharpe,
        "sortino": report.metrics.sortino,
        "max_drawdown": report.metrics.max_drawdown,
        "profit_factor": report.metrics.profit_factor,
        "win_rate": report.metrics.win_rate,
        "average_trade_return": report.average_trade_return,
        "trade_frequency": report.trade_frequency,
        "regime_metrics": {
            k: {
                "sharpe": v.sharpe,
                "sortino": v.sortino,
                "max_drawdown": v.max_drawdown,
                "profit_factor": v.profit_factor,
                "win_rate": v.win_rate,
            }
            for k, v in report.regime_breakdown.items()
        },
    }


def run_paper_sim():
    pipeline = PaperTradingValidationPipeline()
    daily_rows = [sample_day_rows(100 + i) for i in range(30)]
    result = pipeline.simulate("BTC/USDT", "15m", daily_rows, initial_equity=10000)
    return {
        "days": result.days,
        "cycles": result.cycles,
        "executed_orders": result.executed_orders,
        "active_cycles": result.active_cycles,
    }


def main():
    out = {
        "generated_at": datetime.utcnow().isoformat(),
        "pytest": run_pytest(),
        "internal_backtest": run_internal_backtest(),
        "paper_trading": run_paper_sim(),
        "freqtrade_backtest": run_freqtrade_backtest(),
    }

    Path("reports").mkdir(exist_ok=True)
    Path("reports/validation_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
