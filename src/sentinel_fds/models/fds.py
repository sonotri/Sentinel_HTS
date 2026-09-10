from __future__ import annotations

from collections import OrderedDict

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


class FraudMLP(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def train_local_model(
    model: FraudMLP,
    x: np.ndarray,
    y: np.ndarray,
    epochs: int = 2,
    batch_size: int = 128,
    lr: float = 1e-3,
) -> FraudMLP:
    model.train()
    dataset = TensorDataset(torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    pos = max(float(y.sum()), 1.0)
    neg = max(float(len(y) - y.sum()), 1.0)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(neg / pos, dtype=torch.float32))
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for _ in range(epochs):
        for features, labels in loader:
            optimizer.zero_grad()
            loss = criterion(model(features), labels)
            loss.backward()
            optimizer.step()
    return model


@torch.no_grad()
def predict_scores(model: FraudMLP, x: np.ndarray) -> np.ndarray:
    model.eval()
    logits = model(torch.tensor(x, dtype=torch.float32))
    return torch.sigmoid(logits).cpu().numpy()


def get_weights(model: nn.Module) -> OrderedDict[str, torch.Tensor]:
    return OrderedDict((k, v.detach().clone()) for k, v in model.state_dict().items())


def set_weights(model: nn.Module, weights: OrderedDict[str, torch.Tensor]) -> None:
    model.load_state_dict(weights, strict=True)
