from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

from sentinel_fds.models.fds import FraudMLP


@dataclass(frozen=True)
class LeakageResult:
    feature_mse: float
    feature_mae: float
    label_abs_error: float
    gradient_mse: float
    true_label: float
    reconstructed_label: float
    true_score: float
    reconstructed_score: float
    reconstructed_features: np.ndarray


def gradient_leakage_attack(
    model: FraudMLP,
    target_x: np.ndarray,
    target_y: float,
    iterations: int = 120,
    lr: float = 0.08,
    seed: int = 42,
) -> LeakageResult:
    torch.manual_seed(seed)
    model.eval()
    params = [parameter for parameter in model.parameters() if parameter.requires_grad]
    x_true = torch.tensor(target_x.reshape(1, -1), dtype=torch.float32)
    y_true = torch.tensor([float(target_y)], dtype=torch.float32)
    criterion = nn.BCEWithLogitsLoss()

    target_logits = model(x_true)
    target_loss = criterion(target_logits, y_true)
    target_grads = [
        gradient.detach()
        for gradient in torch.autograd.grad(target_loss, params, create_graph=False)
    ]

    dummy_x = torch.randn_like(x_true, requires_grad=True)
    dummy_y_logit = torch.randn(1, requires_grad=True)
    optimizer = torch.optim.Adam([dummy_x, dummy_y_logit], lr=lr)

    gradient_mse = torch.tensor(float("inf"))
    for _ in range(iterations):
        optimizer.zero_grad()
        dummy_y = torch.sigmoid(dummy_y_logit)
        dummy_logits = model(dummy_x)
        dummy_loss = criterion(dummy_logits, dummy_y)
        dummy_grads = torch.autograd.grad(dummy_loss, params, create_graph=True)
        gradient_mse = sum(
            torch.mean((dummy_grad - target_grad) ** 2)
            for dummy_grad, target_grad in zip(dummy_grads, target_grads)
        )
        gradient_mse.backward()
        optimizer.step()

    with torch.no_grad():
        reconstructed_x = dummy_x.detach().cpu().numpy().reshape(-1)
        reconstructed_label = float(torch.sigmoid(dummy_y_logit).item())
        true_features = x_true.cpu().numpy().reshape(-1)
        reconstructed_score = float(torch.sigmoid(model(dummy_x)).item())
        true_score = float(torch.sigmoid(target_logits).item())

    return LeakageResult(
        feature_mse=float(np.mean((reconstructed_x - true_features) ** 2)),
        feature_mae=float(np.mean(np.abs(reconstructed_x - true_features))),
        label_abs_error=abs(reconstructed_label - float(target_y)),
        gradient_mse=float(gradient_mse.detach().item()),
        true_label=float(target_y),
        reconstructed_label=reconstructed_label,
        true_score=true_score,
        reconstructed_score=reconstructed_score,
        reconstructed_features=reconstructed_x,
    )
