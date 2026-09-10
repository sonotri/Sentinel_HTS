from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch

from sentinel_fds.evaluation.metrics import classification_metrics
from sentinel_fds.fl.attacks import SUPPORTED_ATTACKS, poison_labels, poison_weights
from sentinel_fds.fl.secure_aggregation import secure_aggregate_average
from sentinel_fds.models.fds import FraudMLP, get_weights, predict_scores, set_weights, train_local_model
from sentinel_fds.privacy.dp import privatize_update


@dataclass(frozen=True)
class FederatedConfig:
    rounds: int = 5
    local_epochs: int = 2
    batch_size: int = 128
    lr: float = 1e-3
    dp_enabled: bool = True
    clipping_threshold: float = 1.0
    noise_multiplier: float = 0.02
    threshold: float = 0.5
    seed: int = 42
    malicious_banks: tuple[str, ...] = ()
    attack: str = "none"
    attack_scale: float = 5.0
    secure_aggregation: bool = False


def run_federated_training(
    x_train: np.ndarray,
    y_train: np.ndarray,
    bank_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    bank_test: np.ndarray,
    config: FederatedConfig,
) -> tuple[FraudMLP, pd.DataFrame, pd.DataFrame]:
    if config.attack not in SUPPORTED_ATTACKS:
        raise ValueError(f"Unsupported attack: {config.attack}")
    torch.manual_seed(config.seed)
    global_model = FraudMLP(input_dim=x_train.shape[1])

    round_rows = []
    bank_rows = []
    for round_idx in range(1, config.rounds + 1):
        global_weights = get_weights(global_model)
        client_weights = []
        client_sizes = []

        for bank in sorted(set(bank_train)):
            mask = bank_train == bank
            is_malicious = bank in config.malicious_banks
            local_y = poison_labels(y_train[mask], config.attack) if is_malicious else y_train[mask]
            local_model = FraudMLP(input_dim=x_train.shape[1])
            set_weights(local_model, global_weights)
            train_local_model(
                local_model,
                x_train[mask],
                local_y,
                epochs=config.local_epochs,
                batch_size=config.batch_size,
                lr=config.lr,
            )
            weights = get_weights(local_model)
            if is_malicious:
                weights = poison_weights(global_weights, weights, config.attack, config.attack_scale)
            if config.dp_enabled:
                weights = privatize_update(
                    global_weights,
                    weights,
                    clipping_threshold=config.clipping_threshold,
                    noise_multiplier=config.noise_multiplier,
                )
            client_weights.append(weights)
            client_sizes.append(int(mask.sum()))

        secure_stats = {}
        if config.secure_aggregation:
            averaged_weights, secure_stats = secure_aggregate_average(
                client_weights,
                client_sizes,
                seed=config.seed + round_idx,
            )
            set_weights(global_model, averaged_weights)
        else:
            set_weights(global_model, _weighted_average(client_weights, client_sizes))
        scores = predict_scores(global_model, x_test)
        metrics = classification_metrics(y_test, scores, threshold=config.threshold)
        round_rows.append(
            {
                "round": round_idx,
                "malicious_banks": ",".join(config.malicious_banks),
                "attack": config.attack,
                "secure_aggregation": config.secure_aggregation,
                **metrics,
                **secure_stats,
            }
        )

        if round_idx == config.rounds:
            for bank in sorted(set(bank_test)):
                mask = bank_test == bank
                bank_metrics = classification_metrics(y_test[mask], scores[mask], threshold=config.threshold)
                bank_rows.append({"bank": bank, **bank_metrics, "samples": int(mask.sum())})

    return global_model, pd.DataFrame(round_rows), pd.DataFrame(bank_rows)


def _weighted_average(
    weights: list[OrderedDict[str, torch.Tensor]],
    sizes: list[int],
) -> OrderedDict[str, torch.Tensor]:
    total = float(sum(sizes))
    averaged = OrderedDict()
    for key in weights[0]:
        averaged[key] = sum(client[key] * (size / total) for client, size in zip(weights, sizes))
    return averaged
