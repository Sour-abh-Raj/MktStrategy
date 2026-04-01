# Adaptive Multi-Regime Freqtrade Trading System — Technical Specification

Generated: 2026-04-01

## 1) System Architecture

The implementation follows the locked layered architecture:

1. **Data Layer**: ingestion, storage, feature generation, dataset orchestration.
2. **Intelligence Layer**: regime detection (bull/bear/sideways), multi-timeframe context, market state engine.
3. **Strategy Layer**: bull/bear/sideways strategies, strategy evolution engine, validated strategy library.
4. **Decision Layer**: strategy selector, meta-strategy controller, market stress/risk controls, portfolio allocation.
5. **Execution Layer**: exchange gateway, order manager, trade executor, position tracker.
6. **AI Layer**: feature builder, model trainer/evaluator, signal predictor (confirmation).
7. **Optimization Layer**: hyperopt command runner, parameter search, performance validator.
8. **Backtesting Layer**: backtest metrics, walk-forward slicing, performance analysis.
9. **Learning Loop**: performance tracking, retraining schedules, strategy replacement.

## 2) Strategy Design

### Bull strategy
- **Trend breakout** with EMA fast/slow trend filter, RSI momentum, MACD histogram confirmation, volume breakout, ATR stop.

### Bear strategy
- **Breakdown momentum** with bearish EMA structure, RSI weakness, MACD bearishness, downside breakout confirmation, ATR short stop.

### Sideways strategy
- **Bollinger mean reversion** with lower-band entry, middle/upper-band and RSI exit, ATR stop.

### Strategy evolution engine
- Population generation → mutation → crossover → fitness scoring → elite retention across generations.

## 3) Risk Management

- **Trade risk controls**: initial stop loss, trailing stop, breakeven trigger, position-size cap.
- **Portfolio risk controls**: max exposure, max trades per pair, daily loss and drawdown constraints.
- **Market stress module**: volatility shock, price shock, liquidity shock, volume surge detection; normal/elevated/extreme classification.
- **Emergency controller**: can pause system, disable strategies, and close positions under extreme conditions.

## 4) AI Models

- Engineered features include RSI/MACD inputs, MA gap, volume ratio, volatility, momentum.
- Lightweight linear model trainer and evaluator are provided for dependency-light training.
- Predictor outputs:
  - `p_up`
  - `trend_strength`
  - `volatility_shift`
  - confirmation flags (`confirm_long`, `confirm_short`)

## 5) Optimization Process

- Parameter grid generation via `ParameterSearch`.
- Threshold gating via `PerformanceValidator`.
- Freqtrade hyperopt integration wrapper builds/runs:
  - `freqtrade hyperopt --strategy ... --config ... --timerange ... --epochs ...`

## 6) Validation Results

Source: `reports/validation_results.json`

### Unit tests
- `pytest -q` → **6 passed**.

### Backtesting (internal metrics runner)
- Total return: **2.11%**
- Sharpe: **0.4754**
- Sortino: **1.5444**
- Max drawdown: **0.60%**
- Profit factor: **2.9091**
- Win rate: **62.5%**
- Average trade return: **0.2625%**
- Trade frequency: **8**

### Regime breakdown
- Bullish: strong Sharpe and win-rate profile.
- Bearish: weaker profile, higher caution recommended.
- Sideways: positive PF and moderate consistency.

### Paper-trading simulation (30 days replay)
- Cycles: **30**
- Executed orders: **30**
- Active cycles: **30**

### Freqtrade CLI backtest
- Command attempted, but runtime environment lacks `freqtrade` binary.

## 7) Deployment Instructions

1. Install Python dependencies and Freqtrade in target runtime.
2. Place adapter strategy at `user_data/strategies/AdaptiveMetaStrategy.py`.
3. Ingest data via Data Layer or Freqtrade downloader.
4. Run unit tests:
   - `pytest -q`
5. Run validation script:
   - `python scripts/run_validation.py`
6. Run freqtrade backtest (when CLI available):
   - `freqtrade backtesting --strategy AdaptiveMetaStrategy --strategy-path user_data/strategies --timerange 20240101-20241231`
7. Run paper trading pipeline for 30–60 day replay before live enablement.
8. Enable live trading only after risk/validation thresholds are met.

## 8) Deliverables Produced

- Completed module implementations across all requested layers.
- Passing unit test suite.
- Internal backtesting and paper-trading validation outputs.
- Full technical specification report (this document).
