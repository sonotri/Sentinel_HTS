from __future__ import annotations

import argparse
import sys
from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_fds.evaluation.metrics import best_f1_threshold, classification_metrics
from sentinel_fds.models.fds import FraudMLP, predict_scores, train_local_model
from sentinel_fds.models.preprocessing import fit_transform_transactions, transform_transactions
from sentinel_fds.simulation.transactions import SimulationConfig, generate_transactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Flower NumPyClient simulation for Sentinel FDS.")
    parser.add_argument("--samples-per-bank", type=int, default=600)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--local-epochs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    return parser.parse_args()


def main() -> None:
    try:
        import flwr as fl
    except ImportError as exc:
        raise RuntimeError("Install Flower first: python3 -m pip install flwr") from exc

    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    transactions = generate_transactions(SimulationConfig(samples_per_bank=args.samples_per_bank, seed=args.seed))
    train_df, test_df = train_test_split(
        transactions,
        test_size=0.25,
        random_state=args.seed,
        stratify=transactions["is_fraud"],
    )
    train = fit_transform_transactions(train_df)
    test = transform_transactions(test_df, train.transformer)
    banks = sorted(set(train.banks))
    input_dim = train.x.shape[1]

    def get_parameters(model: FraudMLP) -> list[np.ndarray]:
        return [value.detach().cpu().numpy() for value in model.state_dict().values()]

    def set_parameters(model: FraudMLP, parameters: list[np.ndarray]) -> None:
        keys = list(model.state_dict().keys())
        state = OrderedDict((key, torch.tensor(value)) for key, value in zip(keys, parameters))
        model.load_state_dict(state, strict=True)

    class BankClient(fl.client.NumPyClient):
        def __init__(self, bank: str):
            self.bank = bank
            self.model = FraudMLP(input_dim=input_dim)

        def get_parameters(self, config):
            return get_parameters(self.model)

        def fit(self, parameters, config):
            set_parameters(self.model, parameters)
            mask = train.banks == self.bank
            train_local_model(self.model, train.x[mask], train.y[mask], epochs=args.local_epochs)
            return get_parameters(self.model), int(mask.sum()), {}

        def evaluate(self, parameters, config):
            set_parameters(self.model, parameters)
            scores = predict_scores(self.model, test.x)
            threshold, _ = best_f1_threshold(train.y, predict_scores(self.model, train.x))
            metrics = classification_metrics(test.y, scores, threshold=threshold)
            return 1.0 - metrics["f1"], len(test.y), metrics

    def client_fn(context):
        index = int(context.node_config.get("partition-id", 0)) % len(banks)
        return BankClient(banks[index]).to_client()

    strategy = fl.server.strategy.FedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=len(banks),
        min_evaluate_clients=len(banks),
        min_available_clients=len(banks),
    )
    history = fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=len(banks),
        config=fl.server.ServerConfig(num_rounds=args.rounds),
        strategy=strategy,
        ray_init_args={"runtime_env": {"env_vars": {"PYTHONPATH": str(ROOT / "src")}}},
    )
    pd.DataFrame({"history": [str(history)]}).to_csv(args.output_dir / "flower_history.csv", index=False)
    print(f"Flower simulation history written to {(args.output_dir / 'flower_history.csv').resolve()}")


if __name__ == "__main__":
    main()
