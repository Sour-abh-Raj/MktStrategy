from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from freqtrade_project.ai_layer.feature_builder.builder import AIFeatureBuilder
from freqtrade_project.ai_layer.signal_predictor.predictor import AISignalPredictor
from freqtrade_project.data_layer.dataset_manager.manager import DatasetManager
from freqtrade_project.decision_layer.meta_strategy_controller.controller import MetaStrategyController
from freqtrade_project.decision_layer.portfolio_manager.allocation import PortfolioAllocationEngine
from freqtrade_project.decision_layer.risk_manager.market_stress_module.emergency_controller import EmergencyController
from freqtrade_project.decision_layer.risk_manager.market_stress_module.response_engine import StressResponseEngine
from freqtrade_project.decision_layer.risk_manager.market_stress_module.stress_classifier import StressClassifier
from freqtrade_project.decision_layer.risk_manager.market_stress_module.stress_detector import StressDetector
from freqtrade_project.decision_layer.strategy_selector.selector import StrategySelector
from freqtrade_project.decision_layer.strategy_selector.strategy_performance_map_engine.market_state_classifier import state_hash
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
from freqtrade_project.intelligence_layer.market_state_engine.state_engine import MarketStateEngine
from freqtrade_project.strategy_layer.strategy_library.library import StrategyLibrary, StrategyRecord


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

        self.strategy_library = StrategyLibrary()
        for sid, regime in (
            ("bull_trend_breakout", "bullish"),
            ("bear_breakdown_momentum", "bearish"),
            ("sideways_bb_mean_reversion", "sideways"),
        ):
            self.strategy_library.register(StrategyRecord(strategy_id=sid, regime=regime, parameters={}, sharpe=1.1, max_drawdown=0.1, win_rate=0.52))

        ranking = StrategyRankingEngine(self.performance_db, min_trades=1, min_fitness=-10.0)
        self.selector = StrategySelector(ranking, self.strategy_library)
        self.meta = MetaStrategyController(self.selector)
        self.alloc = PortfolioAllocationEngine()
        self.executor = TradeExecutor()

    def warmup_performance_map(self, market_state_hash: str, strategy_ids: List[str]) -> None:
        for sid in strategy_ids:
            self.performance_tracker.record(sid, market_state_hash, trade_return=0.01, drawdown=0.03, won=True)

    def run_cycle(self, cycle: CycleInput) -> Dict[str, object]:
        indicators = self.dataset.ingest(cycle.pair, cycle.timeframe, cycle.raw_rows)
        state = self.state_engine.evaluate(indicators, cycle.tf_scores)
        market_hash = state_hash(state)

        self.warmup_performance_map(market_hash, ["bull_trend_breakout", "bear_breakdown_momentum", "sideways_bb_mean_reversion"])

        ai_features = self.feature_builder.build(indicators)
        ai_signal = self.ai.predict(ai_features)

        stress = self.stress_classifier.classify(self.stress_detector.detect(cycle.stress_metrics))
        risk_profile = self.stress_response.response(stress)
        emergency = self.emergency.evaluate(stress, drawdown=cycle.stress_metrics.get("portfolio_drawdown", 0.0), api_errors=int(cycle.stress_metrics.get("api_errors", 0)))

        plan = self.meta.plan(state, stress)

        if emergency.pause_system:
            plan.active_strategies = []

        allocations = self.alloc.allocate(plan.active_strategies, cycle.equity, risk_profile.max_position_size)
        execution = self.executor.execute_allocations(cycle.pair, allocations, side="long") if allocations else []

        return {
            "market_state": state,
            "market_state_hash": market_hash,
            "ai_signal": ai_signal,
            "stress": stress.value,
            "emergency": emergency,
            "active_strategies": plan.active_strategies,
            "allocations": allocations,
            "execution": execution,
            "halt_new_entries": risk_profile.halt_new_entries,
        }
