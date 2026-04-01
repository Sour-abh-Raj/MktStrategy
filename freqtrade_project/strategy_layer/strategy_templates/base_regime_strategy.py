from __future__ import annotations

from typing import Any, Dict

try:
    from freqtrade.strategy import IStrategy  # type: ignore
except Exception:  # pragma: no cover - local fallback for non-freqtrade envs
    class IStrategy:  # type: ignore
        minimal_roi: Dict[str, float] = {}
        stoploss: float = -0.1
        timeframe: str = "15m"


class BaseRegimeStrategy(IStrategy):
    """Unified base class for regime-specialized Freqtrade strategies."""

    strategy_id: str = "base"
    regime_compatibility: str = "sideways"

    def signal_metadata(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "regime_compatibility": self.regime_compatibility,
        }
