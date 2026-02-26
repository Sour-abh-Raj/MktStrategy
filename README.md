# MktStrategy - NSE F&O OI/IV Abnormality Screener + Backtester

This repository contains a Python implementation of your strategy:

- Scan NSE F&O option contracts close to spot.
- Detect **abnormal Open Interest build-up** and **abnormal Implied Volatility spike**.
- Flag candidate contracts for short-horizon directional trades.
- Backtest with a **1:3 risk-reward structure**.

## Strategy logic implemented

1. Universe: NSE derivative options (`OPTSTK`, `OPTIDX`) from bhavcopy (for backtest) and NSE option-chain API (for live screener).
2. Contract filtering:
   - Near spot (`|strike - spot| / spot <= 8%`).
   - DTE between 2 and 45 days for backtest.
3. Abnormality rules:
   - `Z_OI >= 2.5` on `CHG_IN_OI` (rolling lookback 20 observations).
   - `Z_IV >= 1.5` on implied volatility.
4. Trade model (backtest):
   - Enter at option close on signal day.
   - Stop-loss: `-25%` option premium.
   - Target: `+75%` option premium.
   - Max hold: 5 trading days.

## Installation

```bash
export PYTHONPATH=src
```

No third-party libraries are required.

## Run one-year backtest

```bash
python scripts/run_backtest.py --start 2025-01-01 --end 2025-12-31
```

Outputs:

- `reports/backtest_stats.json`
- `reports/backtest_trades.csv`

### Latest run result (2025-01-01 to 2025-12-31)

- Trades: 26
- Win rate: 61.54%
- Average return/trade: 7.52%
- Median return/trade: 3.95%
- Sum of returns: 195.61%
- Data source used: synthetic fallback (network blocked for NSE archive in this environment)

## Run live screener

```bash
python scripts/run_screener.py --top 30
```

Outputs:

- `reports/live_screen.csv`

If NSE API access is blocked in your environment, the script automatically writes a demo row so you can validate pipeline wiring.

## Production recommendation

For your real 30-minute execution workflow:

- Feed broker/data-vendor intraday option-chain snapshots every 1-5 minutes.
- Reuse `screen_abnormal_contracts` logic and compare current OI/IV against rolling intraday baselines.
- Trigger entries only in last 30 minutes and place bracket orders using the same 1:3 RR template.
