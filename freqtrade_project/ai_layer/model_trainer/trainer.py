from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass
class SimpleLinearModel:
    weights: Dict[str, float]
    bias: float = 0.0

    def predict_score(self, features: Dict[str, float]) -> float:
        return sum(self.weights.get(k, 0.0) * v for k, v in features.items()) + self.bias


class ModelTrainer:
    """Very lightweight trainer to keep project self-contained.

    Learns directional relationships using signed covariance proxy.
    """

    def train_direction_model(self, X: Iterable[Dict[str, float]], y: List[int]) -> SimpleLinearModel:
        X = list(X)
        if not X or not y or len(X) != len(y):
            return SimpleLinearModel(weights={})

        feature_names = list(X[0].keys())
        y_mean = sum(y) / len(y)
        weights: Dict[str, float] = {}

        for name in feature_names:
            xs = [row.get(name, 0.0) for row in X]
            x_mean = sum(xs) / len(xs)
            cov = sum((x - x_mean) * (target - y_mean) for x, target in zip(xs, y)) / max(len(xs), 1)
            weights[name] = cov

        return SimpleLinearModel(weights=weights, bias=-0.5)
