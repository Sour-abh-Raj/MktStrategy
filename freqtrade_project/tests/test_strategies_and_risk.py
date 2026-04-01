from datetime import datetime, timedelta

from freqtrade_project.decision_layer.risk_manager.portfolio_risk_controller import PortfolioRiskController
from freqtrade_project.decision_layer.risk_manager.trade_risk_controller import TradeRiskController
from freqtrade_project.execution_layer.paper_validation.paper_trading_pipeline import PaperTradingValidationPipeline
from freqtrade_project.strategy_layer.bear_strategies.breakdown_momentum import BearBreakdownMomentumStrategy
from freqtrade_project.strategy_layer.bull_strategies.trend_breakout import BullTrendBreakoutStrategy
from freqtrade_project.strategy_layer.sideways_strategies.bb_mean_reversion import SidewaysBBMeanReversionStrategy


def build_series(n=60, up=True):
    p = 100.0
    closes, highs, lows, volumes = [], [], [], []
    for i in range(n):
        p *= 1.003 if up else 0.997
        closes.append(p)
        highs.append(p * 1.002)
        lows.append(p * 0.998)
        volumes.append(1000 + i)
    return closes, highs, lows, volumes


def test_strategy_signal_interfaces():
    c, h, l, v = build_series(up=True)
    bull = BullTrendBreakoutStrategy().evaluate(c, h, l, v)
    bear = BearBreakdownMomentumStrategy().evaluate(c, h, l, v)
    side = SidewaysBBMeanReversionStrategy().evaluate(c, h, l)

    assert "enter" in bull and "atr_stop" in bull
    assert "enter_short" in bear and "atr_stop" in bear
    assert "enter" in side and "exit" in side


def test_risk_controllers_and_paper_pipeline():
    trade_risk = TradeRiskController()
    assert trade_risk.should_move_to_breakeven(0.02)

    portfolio = PortfolioRiskController()
    assert portfolio.allow_new_trade(0.2, "BTC/USDT", {"BTC/USDT": 1}, daily_loss=0.01, drawdown=0.02)

    pipe = PaperTradingValidationPipeline()
    start = datetime(2026, 1, 1)
    day = [
        {
            "timestamp": start + timedelta(minutes=15 * i),
            "open": 100 + i * 0.01,
            "high": 100.2 + i * 0.01,
            "low": 99.8 + i * 0.01,
            "close": 100 + i * 0.01,
            "volume": 1000 + i,
        }
        for i in range(96)
    ]
    result = pipe.simulate("BTC/USDT", "15m", [day for _ in range(30)])
    assert result.days == 30
