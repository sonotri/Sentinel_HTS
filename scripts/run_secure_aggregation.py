from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_fds.evaluation.metrics import best_f1_threshold, classification_metrics
from sentinel_fds.fl.fedavg import FederatedConfig, run_federated_training
from sentinel_fds.models.fds import predict_scores
from sentinel_fds.models.preprocessing import fit_transform_transactions, transform_transactions
from sentinel_fds.simulation.transactions import SimulationConfig, generate_transactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare plain FedAvg and secure aggregation simulation.")
    parser.add_argument("--samples-per-bank", type=int, default=1200)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--local-epochs", type=int, default=1)
    parser.add_argument("--fraud-rate", type=float, default=0.055)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--disable-dp", action="store_true")
    parser.add_argument("--noise-multiplier", type=float, default=0.02)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    transactions = generate_transactions(
        SimulationConfig(
            samples_per_bank=args.samples_per_bank,
            fraud_rate=args.fraud_rate,
            seed=args.seed,
        )
    )
    train_df, test_df = train_test_split(
        transactions,
        test_size=0.25,
        random_state=args.seed,
        stratify=transactions["is_fraud"],
    )
    train = fit_transform_transactions(train_df)
    test = transform_transactions(test_df, train.transformer)

    rows = []
    round_frames = []
    for secure in [False, True]:
        model, round_metrics, _ = run_federated_training(
            train.x,
            train.y,
            train.banks,
            test.x,
            test.y,
            test.banks,
            FederatedConfig(
                rounds=args.rounds,
                local_epochs=args.local_epochs,
                dp_enabled=not args.disable_dp,
                noise_multiplier=args.noise_multiplier,
                seed=args.seed,
                secure_aggregation=secure,
            ),
        )
        train_scores = predict_scores(model, train.x)
        threshold, _ = best_f1_threshold(train.y, train_scores)
        scores = predict_scores(model, test.x)
        metrics = classification_metrics(test.y, scores, threshold=threshold)
        rows.append(
            {
                "mode": "secure_aggregation" if secure else "plain_fedavg",
                **metrics,
            }
        )
        round_metrics.insert(0, "mode", "secure_aggregation" if secure else "plain_fedavg")
        round_frames.append(round_metrics)

    comparison = pd.DataFrame(rows)
    rounds = pd.concat(round_frames, ignore_index=True)
    comparison.to_csv(args.output_dir / "secure_aggregation.csv", index=False)
    rounds.to_csv(args.output_dir / "secure_aggregation_rounds.csv", index=False)
    _write_report(args.output_dir, comparison, rounds)
    print(comparison.to_string(index=False))
    print(f"Secure aggregation results written to {(args.output_dir / 'secure_aggregation.csv').resolve()}")


def _write_report(output_dir: Path, comparison: pd.DataFrame, rounds: pd.DataFrame) -> None:
    report = [
        "# Secure Aggregation Report",
        "",
        "Pairwise masks hide each client update and cancel out in the aggregate.",
        "The final aggregate should match plain FedAvg up to numerical error.",
        "",
        "## Comparison",
        "",
        "```text",
        comparison.to_string(index=False),
        "```",
        "",
        "## Rounds",
        "",
        "```text",
        rounds.to_string(index=False),
        "```",
    ]
    (output_dir / "secure_aggregation_report.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
