from datetime import date, datetime

from freqtrade_project.backtesting_layer.performance_analysis.analyzer import PerformanceAnalyzer
from freqtrade_project.backtesting_layer.walk_forward_testing.walk_forward import WalkForwardTester
from freqtrade_project.execution_layer.paper_validation.paper_trading_pipeline import PaperTradingValidationPipeline
from freqtrade_project.learning_loop.ai_model_retrainer.retrainer import AIModelRetrainer, AIRetrainSchedule
from freqtrade_project.pipeline import AdaptiveTradingSystem, CycleInput


def sample_rows(n: int = 50):
    base = datetime(2026, 1, 1)
    rows = []
    price = 100.0
    for i in range(n):
        price *= 1.001
        rows.append(
            {
                "timestamp": base,
                "open": price * 0.999,
                "high": price * 1.002,
                "low": price * 0.998,
                "close": price,
                "volume": 1000 + i,
            }
        )
    return rows


def test_adaptive_system_cycle_smoke():
    system = AdaptiveTradingSystem()
    result = system.run_cycle(
        CycleInput(
            pair="BTC/USDT",
            timeframe="15m",
            raw_rows=sample_rows(),
            tf_scores={"1d": 0.7, "4h": 0.5, "15m": 0.2},
            stress_metrics={
                "volatility_current": 0.03,
                "volatility_average": 0.02,
                "price_change_5m": 0.01,
                "price_change_15m": 0.02,
                "spread": 0.001,
                "spread_avg": 0.001,
                "volume_ratio": 1.1,
                "portfolio_drawdown": 0.01,
                "api_errors": 0,
            },
            equity=10000,
        )
    )
    assert "market_state" in result
    assert "stress" in result
    assert isinstance(result["execution"], list)


def test_paper_plan_range():
    plan = PaperTradingValidationPipeline().build_plan(date(2026, 1, 1), 45)
    assert plan.days == 45


def test_walk_forward_and_performance():
    slices = WalkForwardTester().generate_slices(data_length=500, train_window=200, test_window=100, step=50)
    assert len(slices) > 0

    metrics = PerformanceAnalyzer().analyze([0.01, -0.005, 0.007, 0.004, -0.002])
    assert metrics.max_drawdown >= 0
    assert metrics.win_rate > 0


def test_ai_retrainer_schedule_due():
    retrainer = AIModelRetrainer()
    schedule = AIRetrainSchedule(last_run=datetime(2026, 1, 1), cadence_days=7)
    assert retrainer.due(schedule, datetime(2026, 1, 10))
