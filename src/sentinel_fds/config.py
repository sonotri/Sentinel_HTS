from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ExperimentConfig:
    samples_per_bank: int = 3000
    rounds: int = 5
    local_epochs: int = 2
    centralized_epochs: int = 10
    fraud_rate: float = 0.055
    seed: int = 42
    dp_enabled: bool = True
    noise_multiplier: float = 0.02
    output_dir: Path = Path("outputs")
    save_artifacts: bool = True


def load_experiment_config(path: Path | None) -> ExperimentConfig:
    if path is None:
        return ExperimentConfig()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Experiment config must be a mapping: {path}")
    return build_experiment_config(data)


def build_experiment_config(overrides: dict[str, Any]) -> ExperimentConfig:
    fields = set(ExperimentConfig.__dataclass_fields__)
    unknown = set(overrides) - fields
    if unknown:
        raise ValueError(f"Unknown experiment config keys: {sorted(unknown)}")
    values = dict(overrides)
    if "output_dir" in values:
        values["output_dir"] = Path(values["output_dir"])
    return ExperimentConfig(**values)


def merge_config(config: ExperimentConfig, overrides: dict[str, Any]) -> ExperimentConfig:
    data = {
        "samples_per_bank": config.samples_per_bank,
        "rounds": config.rounds,
        "local_epochs": config.local_epochs,
        "centralized_epochs": config.centralized_epochs,
        "fraud_rate": config.fraud_rate,
        "seed": config.seed,
        "dp_enabled": config.dp_enabled,
        "noise_multiplier": config.noise_multiplier,
        "output_dir": config.output_dir,
        "save_artifacts": config.save_artifacts,
    }
    data.update({key: value for key, value in overrides.items() if value is not None})
    return build_experiment_config(data)
