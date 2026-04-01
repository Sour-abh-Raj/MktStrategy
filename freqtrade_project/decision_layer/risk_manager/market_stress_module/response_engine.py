from __future__ import annotations

from dataclasses import dataclass

from freqtrade_project.core.interfaces import StressLevel


@dataclass
class RiskProfile:
    max_position_size: float
    max_new_trades: int
    halt_new_entries: bool


class StressResponseEngine:
    def response(self, level: StressLevel) -> RiskProfile:
        if level == StressLevel.EXTREME:
            return RiskProfile(max_position_size=0.0, max_new_trades=0, halt_new_entries=True)
        if level == StressLevel.ELEVATED:
            return RiskProfile(max_position_size=0.05, max_new_trades=2, halt_new_entries=False)
        return RiskProfile(max_position_size=0.10, max_new_trades=10, halt_new_entries=False)
