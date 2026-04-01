from __future__ import annotations

from freqtrade_project.core.interfaces import StressLevel
from freqtrade_project.decision_layer.risk_manager.market_stress_module.stress_detector import StressSignals


class StressClassifier:
    def classify(self, signals: StressSignals) -> StressLevel:
        score = sum(int(v) for v in vars(signals).values())
        if signals.volatility_shock and signals.rapid_price_move:
            return StressLevel.EXTREME
        if score >= 3:
            return StressLevel.EXTREME
        if score >= 1:
            return StressLevel.ELEVATED
        return StressLevel.NORMAL
