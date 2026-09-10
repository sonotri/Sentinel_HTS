from __future__ import annotations

from collections import OrderedDict

import numpy as np
import torch


SUPPORTED_ATTACKS = {"none", "label_flip", "update_scale"}


def poison_labels(labels: np.ndarray, attack: str) -> np.ndarray:
    if attack == "none" or attack == "update_scale":
        return labels
    if attack == "label_flip":
        return 1.0 - labels
    raise ValueError(f"Unsupported attack: {attack}")


def poison_weights(
    global_weights: OrderedDict[str, torch.Tensor],
    local_weights: OrderedDict[str, torch.Tensor],
    attack: str,
    scale: float,
) -> OrderedDict[str, torch.Tensor]:
    if attack in {"none", "label_flip"}:
        return local_weights
    if attack != "update_scale":
        raise ValueError(f"Unsupported attack: {attack}")
    return OrderedDict(
        (key, global_weights[key] + scale * (local_weights[key] - global_weights[key]))
        for key in global_weights
    )
