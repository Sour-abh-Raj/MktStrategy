#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from mktstrategy.backtester import BacktestConfig, prepare_signals, run_backtest
from mktstrategy.data import download_fo_bhavcopy, generate_synthetic_fo_data, load_fo_dataset


def _write_trades(path: str, trades: list[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not trades:
        p.write_text("", encoding="utf-8")
        return
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(trades[0].keys()))
        w.writeheader()
        w.writerows(trades)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NSE options OI/IV anomaly backtest")
    parser.add_argument("--start", default=(date.today().replace(year=date.today().year - 1)).isoformat())
    parser.add_argument("--end", default=date.today().isoformat())
    parser.add_argument("--data-dir", default="data/fo_bhav")
    parser.add_argument("--stats-out", default="reports/backtest_stats.json")
    parser.add_argument("--trades-out", default="reports/backtest_trades.csv")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)

    print(f"Downloading FO bhavcopy from {start} to {end}...")
    dl_stats = download_fo_bhavcopy(start, end, args.data_dir)
    print(f"Download stats: downloaded={dl_stats.downloaded}, skipped={dl_stats.skipped}, failed={dl_stats.failed}")

    data_source = "nse_bhavcopy"
    try:
        rows = load_fo_dataset(args.data_dir)
    except FileNotFoundError:
        rows = generate_synthetic_fo_data(start, end)
        data_source = "synthetic"

    signals = prepare_signals(rows, BacktestConfig())
    trades, stats = run_backtest(signals, BacktestConfig())
    stats["data_source"] = data_source

    Path(args.stats_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.stats_out).write_text(json.dumps(stats, indent=2), encoding="utf-8")
    _write_trades(args.trades_out, trades)

    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
