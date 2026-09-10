from __future__ import annotations

from collections import OrderedDict

import torch


StateDict = OrderedDict[str, torch.Tensor]


def flatten_weights(weights: StateDict) -> torch.Tensor:
    return torch.cat([tensor.detach().reshape(-1).float() for tensor in weights.values()])


def unflatten_weights(template: StateDict, vector: torch.Tensor) -> StateDict:
    restored = OrderedDict()
    offset = 0
    for key, tensor in template.items():
        size = tensor.numel()
        restored[key] = vector[offset : offset + size].reshape(tensor.shape).to(dtype=tensor.dtype)
        offset += size
    return restored


def secure_aggregate_average(
    client_weights: list[StateDict],
    sizes: list[int],
    seed: int = 42,
) -> tuple[StateDict, dict[str, float]]:
    """Pairwise-mask secure aggregation simulation.

    The server sees masked client vectors. Pairwise masks cancel in the sum, so
    the final weighted average matches plain FedAvg while individual updates are
    hidden from direct inspection.
    """
    if not client_weights:
        raise ValueError("client_weights must not be empty.")
    if len(client_weights) != len(sizes):
        raise ValueError("client_weights and sizes length mismatch.")

    vectors = [flatten_weights(weights) for weights in client_weights]
    total = float(sum(sizes))
    weighted_vectors = [vector * (size / total) for vector, size in zip(vectors, sizes)]
    generator = torch.Generator().manual_seed(seed)
    masked_vectors = [vector.clone() for vector in weighted_vectors]

    for i in range(len(masked_vectors)):
        for j in range(i + 1, len(masked_vectors)):
            mask = torch.randn(masked_vectors[i].shape, generator=generator)
            masked_vectors[i] = masked_vectors[i] + mask
            masked_vectors[j] = masked_vectors[j] - mask

    secure_sum = sum(masked_vectors)
    plain_sum = sum(weighted_vectors)
    reconstruction_error = torch.mean((secure_sum - plain_sum) ** 2).item()
    mask_norm = torch.mean(torch.stack([torch.norm(masked - plain) for masked, plain in zip(masked_vectors, weighted_vectors)])).item()
    return (
        unflatten_weights(client_weights[0], secure_sum),
        {
            "reconstruction_mse": float(reconstruction_error),
            "mean_mask_delta_norm": float(mask_norm),
            "clients": float(len(client_weights)),
        },
    )
