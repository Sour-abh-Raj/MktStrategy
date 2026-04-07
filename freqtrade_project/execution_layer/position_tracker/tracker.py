from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Position:
    pair: str
    side: str
    size: float


class PositionTracker:
    def __init__(self) -> None:
        self.positions: Dict[str, Position] = {}

    def update(self, position: Position) -> None:
        self.positions[position.pair] = position

    def exposure(self) -> float:
        return sum(abs(p.size) for p in self.positions.values())
