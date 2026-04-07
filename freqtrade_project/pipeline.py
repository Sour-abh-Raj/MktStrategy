from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from freqtrade_project.ai_layer.feature_builder.builder import AIFeatureBuilder
from freqtrade_project.ai_layer.signal_predictor.predictor import AISignalPredictor
from freqtrade_project.config.strategy_config_loader import get_strategy_config
from freqtrade_project.data_layer.dataset_manager.manager import DatasetManager
from freqtrade_project.decision_layer.meta_strategy_controller.controller import (
    MetaStrategyController,
)
from freqtrade_project.decision_layer.portfolio_manager.allocation import (
    PortfolioAllocationEngine,
)
from freqtrade_project.decision_layer.risk_manager.market_stress_module.emergency_controller import (
    EmergencyController,
)
from freqtrade_project.decision_layer.risk_manager.market_stress_module.response_engine import (
    StressResponseEngine,
)
from freqtrade_project.decision_layer.risk_manager.market_stress_module.stress_classifier import (
    StressClassifier,
)
from freqtrade_project.decision_layer.risk_manager.market_stress_module.stress_detector import (
    StressDetector,
)
from freqtrade_project.decision_layer.strategy_selector.selector import StrategySelector
from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.market_state_classifier import (
    state_hash,
)
from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.regime_performance_database import (
    RegimePerformanceDatabase,
)
from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.strategy_performance_tracker import (
    StrategyPerformanceTracker,
)
from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.strategy_ranking_engine import (
    StrategyRankingEngine,
)
from freqtrade_project.execution_layer.trade_executor.executor import TradeExecutor
from freqtrade_project.intelligence_layer.market_state_engine.state_engine import (
    MarketStateEngine,
)
from freqtrade_project.strategy_layer.strategy_library.library import (
    StrategyLibrary,
    StrategyRecord,
)


@dataclass
class CycleInput:
    pair: str
    timeframe: str
    raw_rows: Iterable[dict]
    tf_scores: Dict[str, float]
    stress_metrics: Dict[str, float]
    equity: float


class AdaptiveTradingSystem:
    def __init__(self) -> None:
        self.dataset = DatasetManager()
        self.state_engine = MarketStateEngine()
        self.feature_builder = AIFeatureBuilder()
        self.ai = AISignalPredictor()
        self.stress_detector = StressDetector()
        self.stress_classifier = StressClassifier()
        self.stress_response = StressResponseEngine()
        self.emergency = EmergencyController()

        self.performance_db = RegimePerformanceDatabase()
        self.performance_tracker = StrategyPerformanceTracker(self.performance_db)

        # Load strategies from configuration
        self.strategy_library = StrategyLibrary()
        config = get_strategy_config()
        
        for strat_config in config.get_all_strategies():
            self.strategy_library.register(
                StrategyRecord(
                    strategy_id=strat_config.strategy_id,
                    regime=strat_config.regime,
                    parameters=strat_config.parameters,
                    sharpe=1.1,
                    max_drawdown=0.1,
                    win_rate=0.52,
                )
            )

        ranking = StrategyRankingEngine(self.performance_db, min_trades=1)
        self.selector = StrategySelector(ranking, self.strategy_library)
        self.meta = MetaStrategyController(self.selector)
        self.alloc = PortfolioAllocationEngine()
        self.executor = TradeExecutor()

    def warmup_performance_map(
        self, market_state_hash: str, strategy_ids: List[str]
    ) -> None:
        # If no strategy_ids provided, use all enabled from config
        if not strategy_ids:
            config = get_strategy_config()
            strategy_ids = config.get_enabled_strategy_ids()
        
        for sid in strategy_ids:
            self.performance_tracker.record(
                sid, market_state_hash, trade_return=0.01, drawdown=0.03, won=True
            )

    def run_cycle(self, cycle: CycleInput) -> Dict[str, object]:
        """Execute complete trading cycle with fault tolerance and deterministic behavior."""
        try:
            # Phase 1: Data Ingestion (fault tolerant)
            indicators = self.dataset.ingest(
                cycle.pair, cycle.timeframe, cycle.raw_rows
            )
            if not indicators:
                return self._error_response("Data ingestion failed - insufficient data")

            # Phase 2: Intelligence Layer (regime detection)
            state = self.state_engine.evaluate(indicators, cycle.tf_scores)
            market_hash = state_hash(state)

            # Warm up performance tracking for known strategies
            self.warmup_performance_map(
                market_hash,
                [
                    "bull_trend_breakout",
                    "bear_breakdown_momentum",
                    "sideways_bb_mean_reversion",
                    "vol_options_strategies_gen_1",
                    "carry_trend_following_gen_1",
                ],
            )

            # Phase 3: AI Signal Filtering
            ai_features = self.feature_builder.build(indicators)
            ai_signal = self.ai.predict(ai_features)

            # Phase 4: Risk Assessment
            stress_metrics = cycle.stress_metrics or {}
            stress_signals = self.stress_detector.detect(stress_metrics)
            stress = self.stress_classifier.classify(stress_signals)
            risk_profile = self.stress_response.response(stress)
            emergency = self.emergency.evaluate(
                stress,
                drawdown=stress_metrics.get("portfolio_drawdown", 0.0),
                api_errors=int(stress_metrics.get("api_errors", 0)),
            )

            # Phase 5: Strategy Selection
            plan = self.meta.plan(state, stress)

            # Emergency override: halt all trading if system is stressed
            if emergency.pause_system:
                plan.active_strategies = []

            # Phase 6: Portfolio Allocation (deterministic based on risk profile)
            allocations = self.alloc.allocate(
                plan.active_strategies, cycle.equity, risk_profile.max_position_size
            )

            # Phase 7: Execution
            execution = (
                self.executor.execute_allocations(cycle.pair, allocations, side="long")
                if allocations
                else []
            )

            # Success response with complete cycle data
            raw_rows_list = list(cycle.raw_rows) if cycle.raw_rows else []
            return {
                "success": True,
                "market_state": state,
                "market_state_hash": market_hash,
                "ai_signal": ai_signal,
                "stress": stress.value,
                "emergency": emergency,
                "active_strategies": plan.active_strategies,
                "allocations": allocations,
                "execution": execution,
                "halt_new_entries": risk_profile.halt_new_entries,
                "cycle_timestamp": raw_rows_list[-1].get("timestamp")
                if raw_rows_list
                else None,
            }

        except Exception as e:
            # Fault tolerant: return error state instead of crashing
            return self._error_response(f"Pipeline error: {str(e)}")

    def _error_response(self, message: str) -> Dict[str, object]:
        """Return safe error response that doesn't break downstream processing."""
        return {
            "success": False,
            "error": message,
            "market_state": None,
            "market_state_hash": None,
            "ai_signal": None,
            "stress": "normal",
            "emergency": None,
            "active_strategies": [],
            "allocations": {},
            "execution": [],
            "halt_new_entries": False,
            "cycle_timestamp": None,
        }
