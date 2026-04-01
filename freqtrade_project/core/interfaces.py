from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Protocol


class Trend(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class VolatilityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MomentumState(str, Enum):
    STRONG = "strong"
    WEAK = "weak"
    REVERSAL = "reversal"


class LiquidityState(str, Enum):
    HIGH = "high"
    LOW = "low"


class StressLevel(str, Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    EXTREME = "extreme"


@dataclass(frozen=True)
class MarketState:
    trend: Trend
    volatility: VolatilityLevel
    momentum: MomentumState
    liquidity: LiquidityState
    regime: str
    context_score: float


@dataclass(frozen=True)
class StrategySignal:
    strategy_id: str
    pair: str
    side: str
    confidence: float
    metadata: Dict[str, float]


class MarketStateClassifier(Protocol):
    def classify(self, indicators: Dict[str, float]) -> MarketState:
        ...


class StrategySignalProvider(Protocol):
    def generate(self, market_state: MarketState, pair: str) -> List[StrategySignal]:
        ...


class RiskController(Protocol):
    def apply(self, signal: StrategySignal, stress_level: StressLevel) -> StrategySignal | None:
        ...


class AllocationEngine(Protocol):
    def allocate(self, signals: List[StrategySignal], equity: float) -> Dict[str, float]:
        ...


class ExecutionGateway(Protocol):
    def execute(self, allocations: Dict[str, float]) -> None:
        ...
