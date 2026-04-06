#!/usr/bin/env bash
set -euo pipefail

# Data init
freqtrade download-data \
  --exchange binance \
  --timeframes 5m \
  --pairs BTC/USDT ETH/USDT

# Backtesting
freqtrade backtesting \
  --strategy AdaptiveMetaStrategy \
  --strategy-path user_data/strategies \
  --timerange 20220101-20241231 \
  --timeframe 5m

# Hyperopt
freqtrade hyperopt \
  --strategy AdaptiveMetaStrategy \
  --epochs 50

# Trade (dry-run first)
freqtrade trade \
  --strategy AdaptiveMetaStrategy \
  --config config/config.json
