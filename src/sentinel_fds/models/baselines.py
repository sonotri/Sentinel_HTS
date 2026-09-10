from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from sentinel_fds.evaluation.metrics import (
    best_f1_threshold,
    classification_metrics,
    classification_metrics_from_predictions,
)
from sentinel_fds.models.fds import FraudMLP, predict_scores, train_local_model


def train_centralized_baseline(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
) -> tuple[FraudMLP, dict[str, float]]:
    torch.manual_seed(seed)
    model = FraudMLP(input_dim=x_train.shape[1])
    train_local_model(model, x_train, y_train, epochs=epochs, batch_size=batch_size, lr=lr)
    threshold, _ = best_f1_threshold(y_train, predict_scores(model, x_train))
    return model, classification_metrics(y_test, predict_scores(model, x_test), threshold=threshold)


def train_local_only_baseline(
    x_train: np.ndarray,
    y_train: np.ndarray,
    bank_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    bank_test: np.ndarray,
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
) -> tuple[dict[str, float], pd.DataFrame]:
    scores = np.zeros(len(y_test), dtype=np.float32)
    predictions = np.zeros(len(y_test), dtype=np.int64)
    bank_rows = []

    for offset, bank in enumerate(sorted(set(bank_train))):
        torch.manual_seed(seed + offset)
        train_mask = bank_train == bank
        test_mask = bank_test == bank
        model = FraudMLP(input_dim=x_train.shape[1])
        train_local_model(
            model,
            x_train[train_mask],
            y_train[train_mask],
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
        )
        train_scores = predict_scores(model, x_train[train_mask])
        threshold, _ = best_f1_threshold(y_train[train_mask], train_scores)
        bank_scores = predict_scores(model, x_test[test_mask])
        scores[test_mask] = bank_scores
        predictions[test_mask] = (bank_scores >= threshold).astype(int)
        bank_metrics = classification_metrics(y_test[test_mask], bank_scores, threshold=threshold)
        bank_rows.append({"model": "Local-only", "bank": bank, **bank_metrics, "samples": int(test_mask.sum())})

    overall = classification_metrics_from_predictions(y_test, scores, predictions)
    overall["threshold"] = float("nan")
    return overall, pd.DataFrame(bank_rows)
