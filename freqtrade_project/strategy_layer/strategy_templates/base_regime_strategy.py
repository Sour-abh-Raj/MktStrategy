from __future__ import annotations

from typing import Any, Dict

# Import IStrategy with fallback for non-freqtrade environments
try:
    from freqtrade.strategy import IStrategy  # type: ignore
except ImportError:
    # Define minimal interface for development/testing
    class IStrategy:  # type: ignore[no-redef]
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
