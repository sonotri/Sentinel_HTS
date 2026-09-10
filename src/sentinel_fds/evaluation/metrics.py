from __future__ import annotations

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score


def classification_metrics(y_true: np.ndarray, scores: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)
    predictions = (scores >= threshold).astype(int)
    return classification_metrics_from_predictions(y_true, scores, predictions) | {"threshold": threshold}


def classification_metrics_from_predictions(
    y_true: np.ndarray,
    scores: np.ndarray,
    predictions: np.ndarray,
) -> dict[str, float]:
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)
    predictions = np.asarray(predictions)
    metrics = {
        "precision": precision_score(y_true, predictions, zero_division=0),
        "recall": recall_score(y_true, predictions, zero_division=0),
        "f1": f1_score(y_true, predictions, zero_division=0),
    }
    if len(np.unique(y_true)) == 2:
        metrics["roc_auc"] = roc_auc_score(y_true, scores)
    else:
        metrics["roc_auc"] = float("nan")
    return metrics


def threshold_curve(y_true: np.ndarray, scores: np.ndarray, steps: int = 101) -> list[dict[str, float]]:
    thresholds = np.linspace(0.01, 0.99, steps)
    return [
        {"threshold": float(threshold), **classification_metrics(y_true, scores, float(threshold))}
        for threshold in thresholds
    ]


def best_f1_threshold(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, dict[str, float]]:
    rows = threshold_curve(y_true, scores)
    best = max(rows, key=lambda row: (row["f1"], row["recall"], row["precision"]))
    return float(best["threshold"]), best
