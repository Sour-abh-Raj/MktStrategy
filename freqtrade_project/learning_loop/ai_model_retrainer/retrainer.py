from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class AIRetrainSchedule:
    last_run: datetime
    cadence_days: int = 7


class AIModelRetrainer:
    def due(self, schedule: AIRetrainSchedule, now: datetime) -> bool:
        return now >= schedule.last_run + timedelta(days=schedule.cadence_days)
