from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RetrainSchedule:
    last_run: datetime
    cadence_days: int


class StrategyRetrainer:
    def due(self, schedule: RetrainSchedule, now: datetime) -> bool:
        return now >= schedule.last_run + timedelta(days=schedule.cadence_days)
