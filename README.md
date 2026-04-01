# Adaptive Multi-Regime Freqtrade System

This repository implements a modular, risk-first adaptive trading architecture designed for Freqtrade + Binance workflows.

## Locked Architecture (Implemented)

- **Layer 1: Data Layer**
  - `data_layer/data_collector/binance_collector.py`
  - `data_layer/historical_data_store/store.py`
  - `data_layer/feature_engineering/engine.py`
  - `data_layer/dataset_manager/manager.py`
- **Layer 2: Intelligence Layer**
  - Regime detection + market-state vector + multi-timeframe context
- **Layer 3: Strategy Layer**
  - Bull / Bear / Sideways strategies
  - Strategy evolution engine (generator, mutation, crossover, fitness, controller)
  - Strategy library with validation gates
- **Layer 4: Decision Layer**
  - Meta strategy controller
  - Strategy selector + strategy performance market map
  - Risk manager + market stress module + emergency controls
  - Portfolio allocator
- **Layer 5: Execution Layer**
  - Exchange interface
  - Order manager
  - Trade executor
  - Position tracker
  - 30-60 day paper-trading validation pipeline
- **AI Layer**
  - Feature builder, model trainer, evaluator, signal predictor (confirmation layer)
- **Optimization / Backtesting / Learning Loop**
  - Hyperopt runner, parameter search, performance validator
  - Backtest runner, walk-forward slicing, performance analyzer
  - Performance tracker, AI retrainer, strategy retrainer, replacement engine

## End-to-End Orchestration

Main entrypoint:

- `freqtrade_project/pipeline.py`

Pipeline flow:

1. Ingest market data
2. Build engineered features
3. Detect market regime / market state
4. Query strategy performance map + select/rank strategies
5. Apply AI confirmation layer
6. Apply stress/risk checks + emergency overrides
7. Allocate capital
8. Execute (paper/live gateway adapter)

## Current Status

This is a robust, test-covered implementation scaffold intended to be wired directly into a full Freqtrade runtime (strategy callbacks, exchange execution, hyperopt jobs, and FreqAI model persistence).
