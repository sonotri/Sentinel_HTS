from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_fds.evaluation.metrics import best_f1_threshold, classification_metrics
from sentinel_fds.models.fds import predict_scores
from sentinel_fds.models.preprocessing import fit_transform_transactions, transform_transactions
from sentinel_fds.privacy.opacus_training import train_with_opacus
from sentinel_fds.simulation.transactions import SimulationConfig, generate_transactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train centralized DP-SGD baseline with Opacus.")
    parser.add_argument("--samples-per-bank", type=int, default=1200)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--noise-multiplier", type=float, default=1.0)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--delta", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    return parser.parse_args()


def main() -> None:
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
    model, epsilon = train_with_opacus(
        train.x,
        train.y,
        epochs=args.epochs,
        noise_multiplier=args.noise_multiplier,
        max_grad_norm=args.max_grad_norm,
        delta=args.delta,
    )
    train_scores = predict_scores(model, train.x)
    threshold, _ = best_f1_threshold(train.y, train_scores)
    scores = predict_scores(model, test.x)
    metrics = classification_metrics(test.y, scores, threshold=threshold)
    result = pd.DataFrame(
        [
            {
                "epsilon": epsilon,
                "delta": args.delta,
                "noise_multiplier": args.noise_multiplier,
                "max_grad_norm": args.max_grad_norm,
                "epochs": args.epochs,
                **metrics,
            }
        ]
    )
    result.to_csv(args.output_dir / "opacus_dp.csv", index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
