from __future__ import annotations

from typing import Dict, Iterable, List

from freqtrade_project.ai_layer.model_trainer.trainer import SimpleLinearModel


class ModelEvaluator:
    def evaluate_accuracy(self, model: SimpleLinearModel, X: Iterable[Dict[str, float]], y: List[int]) -> float:
        X = list(X)
        if not X or not y:
            return 0.0
        correct = 0
        for row, target in zip(X, y):
            pred = 1 if model.predict_score(row) > 0 else 0
            correct += int(pred == target)
        return correct / len(y)
