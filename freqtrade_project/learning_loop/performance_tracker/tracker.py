from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class PerformanceSnapshot:
    timestamp: datetime
    equity: float
    drawdown: float


class PerformanceTracker:
    def __init__(self) -> None:
        self.history: List[PerformanceSnapshot] = []

    def log(self, equity: float, drawdown: float) -> None:
        self.history.append(PerformanceSnapshot(datetime.utcnow(), equity, drawdown))
