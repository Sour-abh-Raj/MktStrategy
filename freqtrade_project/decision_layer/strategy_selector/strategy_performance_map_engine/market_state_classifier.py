from __future__ import annotations

from freqtrade_project.core.interfaces import MarketState


def state_hash(state: MarketState) -> str:
    return f"{state.regime}|{state.trend.value}|{state.volatility.value}|{state.momentum.value}|{state.liquidity.value}"
