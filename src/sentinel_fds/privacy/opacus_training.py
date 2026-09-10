from __future__ import annotations

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from sentinel_fds.models.fds import FraudMLP


def train_with_opacus(
    x: np.ndarray,
    y: np.ndarray,
    epochs: int = 3,
    batch_size: int = 128,
    lr: float = 1e-3,
    noise_multiplier: float = 1.0,
    max_grad_norm: float = 1.0,
    delta: float = 1e-5,
) -> tuple[FraudMLP, float]:
    try:
        from opacus import PrivacyEngine
    except ImportError as exc:
        raise RuntimeError("Install Opacus first: python3 -m pip install opacus") from exc

    model = FraudMLP(input_dim=x.shape[1])
    dataset = TensorDataset(torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    pos = max(float(y.sum()), 1.0)
    neg = max(float(len(y) - y.sum()), 1.0)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(neg / pos, dtype=torch.float32))
    privacy_engine = PrivacyEngine()
    model, optimizer, loader = privacy_engine.make_private(
        module=model,
        optimizer=optimizer,
        data_loader=loader,
        noise_multiplier=noise_multiplier,
        max_grad_norm=max_grad_norm,
    )

    model.train()
    for _ in range(epochs):
        for features, labels in loader:
            optimizer.zero_grad()
            loss = criterion(model(features), labels)
            loss.backward()
            optimizer.step()

    epsilon = float(privacy_engine.get_epsilon(delta))
    return model, epsilon
