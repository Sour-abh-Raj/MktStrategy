from __future__ import annotations

from freqtrade_project.core.interfaces import StressLevel
from freqtrade_project.decision_layer.risk_manager.market_stress_module.stress_detector import StressSignals


class StressClassifier:
    """Classifies a StressSignals snapshot into a StressLevel enum."""

    def classify(self, signals: StressSignals) -> StressLevel:
        # Use explicit field access rather than vars() for robustness
        score = sum([
            int(signals.volatility_shock),
            int(signals.rapid_price_move),
            int(signals.liquidity_shock),
            int(signals.volume_surge),
        ])

        # Extreme: two core danger signals fire simultaneously
        if signals.volatility_shock and signals.rapid_price_move:
            return StressLevel.EXTREME
        # Extreme: three or more signals
        if score >= 3:
            return StressLevel.EXTREME
        # Elevated: at least one signal
        if score >= 1:
            return StressLevel.ELEVATED
        return StressLevel.NORMAL
