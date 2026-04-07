from __future__ import annotations

from typing import Dict, Iterable


class PortfolioAllocationEngine:
    """Allocates equity across active strategies with a hard exposure cap.

    Rules:
    - Equal-weight allocation per strategy.
    - Per-strategy allocation capped at `max_position_size * equity`.
    - Total deployed capital capped at `max_total_exposure` (default 70 %) of equity.
    """

    MAX_TOTAL_EXPOSURE: float = 0.70  # 70 % of equity maximum

    def allocate(
        self,
        strategies: Iterable[str],
        equity: float,
        max_position_size: float,
    ) -> Dict[str, float]:
        strategies = list(strategies)
        if not strategies or equity <= 0:
            return {}

        # Per-strategy cap from risk profile
        per_strategy_cap = equity * max(min(max_position_size, 1.0), 0.0)

        # Equal-weight share
        equal_share = equity / len(strategies)
        per = min(equal_share, per_strategy_cap)

        # Total exposure guard — scale down if total would exceed limit
        total_deployable = equity * self.MAX_TOTAL_EXPOSURE
        if per * len(strategies) > total_deployable:
            per = total_deployable / len(strategies)

        return {s: round(per, 2) for s in strategies}
