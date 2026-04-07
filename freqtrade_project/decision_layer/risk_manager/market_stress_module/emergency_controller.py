from __future__ import annotations

from dataclasses import dataclass

from freqtrade_project.core.interfaces import StressLevel


@dataclass
class EmergencyAction:
    close_positions: bool
    disable_strategies: bool
    pause_system: bool


class EmergencyController:
    def evaluate(self, level: StressLevel, drawdown: float, api_errors: int) -> EmergencyAction:
        if level == StressLevel.EXTREME or drawdown > 0.18 or api_errors >= 3:
            return EmergencyAction(True, True, True)
        return EmergencyAction(False, False, False)
