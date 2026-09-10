from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from math import log, sqrt

import torch


def privatize_update(
    global_weights: OrderedDict[str, torch.Tensor],
    local_weights: OrderedDict[str, torch.Tensor],
    clipping_threshold: float,
    noise_multiplier: float,
) -> OrderedDict[str, torch.Tensor]:
    update = OrderedDict((key, local_weights[key] - global_weights[key]) for key in global_weights)
    total_norm = torch.sqrt(sum(torch.sum(tensor.float() ** 2) for tensor in update.values()))
    scale = min(1.0, clipping_threshold / (float(total_norm) + 1e-12))

    privatized = OrderedDict()
    for key, delta in update.items():
        clipped = delta * scale
        if noise_multiplier > 0:
            noise = torch.normal(
                mean=0.0,
                std=clipping_threshold * noise_multiplier,
                size=clipped.shape,
                device=clipped.device,
            )
            clipped = clipped + noise
        privatized[key] = global_weights[key] + clipped
    return privatized


@dataclass(frozen=True)
class PrivacyEstimate:
    epsilon: float
    delta: float
    sampling_rate: float
    steps: int
    noise_multiplier: float
    note: str


def estimate_gaussian_epsilon(
    *,
    noise_multiplier: float,
    sampling_rate: float,
    steps: int,
    delta: float = 1e-5,
) -> PrivacyEstimate:
    """Return a conservative rough epsilon estimate for the demo accountant.

    This is not a replacement for Opacus/RDP accounting. It gives the dashboard a
    stable privacy/performance signal until the project moves to sample-level
    DP-SGD.
    """
    if noise_multiplier <= 0:
        return PrivacyEstimate(
            epsilon=float("inf"),
            delta=delta,
            sampling_rate=sampling_rate,
            steps=steps,
            noise_multiplier=noise_multiplier,
            note="No DP noise; privacy budget is unbounded.",
        )
    if not 0 < sampling_rate <= 1:
        raise ValueError("sampling_rate must be in (0, 1].")
    if steps < 1:
        raise ValueError("steps must be positive.")
    if not 0 < delta < 1:
        raise ValueError("delta must be in (0, 1).")

    base = sampling_rate * sqrt(2 * steps * log(1 / delta)) / noise_multiplier
    second_order = steps * (sampling_rate**2) / (noise_multiplier**2)
    epsilon = base + second_order
    return PrivacyEstimate(
        epsilon=float(epsilon),
        delta=delta,
        sampling_rate=sampling_rate,
        steps=steps,
        noise_multiplier=noise_multiplier,
        note="Approximate demo accountant; use Opacus/RDP for formal DP claims.",
    )
