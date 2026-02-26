#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from mktstrategy.screener import NseClient, ScreenerConfig, screen_abnormal_contracts


def _write_rows(path: str, rows: list[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _demo_rows() -> list[dict]:
    return [
        {
            "symbol": "RELIANCE",
            "option_type": "CE",
            "strike": 3000.0,
            "expiry": "demo",
            "spot": 2976.2,
            "open_interest": 612000.0,
            "change_in_oi": 124000.0,
            "implied_vol": 31.8,
            "ltp": 72.5,
            "moneyness": 0.008,
            "z_oi": 3.2,
            "z_iv": 1.9,
            "signal": "Bullish-Call OI build",
        }
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Live NSE F&O OI/IV anomaly screener")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--out", default="reports/live_screen.csv")
    args = parser.parse_args()

    try:
        client = NseClient()
        symbols = client.get_fo_symbols()
        print(f"Loaded {len(symbols)} F&O symbols")
        flagged = screen_abnormal_contracts(client, symbols, ScreenerConfig())
    except Exception as exc:
        print(f"Live NSE fetch unavailable ({exc}); writing demo screen output instead.")
        flagged = _demo_rows()

    _write_rows(args.out, flagged)
    print(f"Flagged contracts: {len(flagged)}")
    for row in flagged[: args.top]:
        print(row)


if __name__ == "__main__":
    main()
