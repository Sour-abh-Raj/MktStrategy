from __future__ import annotations

from typing import Dict

from freqtrade_project.ai_layer.model_trainer.trainer import SimpleLinearModel


class AISignalPredictor:
    """AI confirmation layer outputting direction probability and confidence flags."""

    def __init__(self, model: SimpleLinearModel | None = None) -> None:
        self.model = model or SimpleLinearModel(weights={"momentum_score": 1.2, "macd_hist": 0.8, "volatility": -1.0})

    def predict(self, features: Dict[str, float]) -> Dict[str, float]:
        score = self.model.predict_score(features)
        p_up = 1 / (1 + (2.71828 ** (-score)))
        trend_strength = min(max(abs(features.get("ma_gap", 0.0)) * 200, 0.0), 1.0)
        vol_shift = features.get("volatility", 0.02) - features.get("volatility_baseline", 0.02)
        confirm_long = 1.0 if p_up >= 0.55 and trend_strength >= 0.2 else 0.0
        confirm_short = 1.0 if p_up <= 0.45 and trend_strength >= 0.2 else 0.0
        return {
            "p_up": round(p_up, 4),
            "trend_strength": round(trend_strength, 4),
            "volatility_shift": round(vol_shift, 6),
            "confirm_long": confirm_long,
            "confirm_short": confirm_short,
        }
