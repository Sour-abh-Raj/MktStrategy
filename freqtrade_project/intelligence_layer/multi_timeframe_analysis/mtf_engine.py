from __future__ import annotations

from typing import Dict


class MultiTimeframeAnalysisEngine:
    """Combines macro(1D), mid(4H), micro(15m) trend signals into one score."""

    WEIGHTS = {"1d": 0.5, "4h": 0.3, "15m": 0.2}

    def compute_context_score(self, tf_metrics: Dict[str, float]) -> float:
        score = 0.0
        for tf, weight in self.WEIGHTS.items():
            score += tf_metrics.get(tf, 0.0) * weight
        return round(score, 4)
