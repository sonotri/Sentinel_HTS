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
from sentinel_fds.privacy.dp import estimate_gaussian_epsilon
from sentinel_fds.simulation.transactions import SimulationConfig, generate_transactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DP noise multiplier sweep for Sentinel FL.")
    parser.add_argument("--samples-per-bank", type=int, default=1200)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--local-epochs", type=int, default=1)
    parser.add_argument("--fraud-rate", type=float, default=0.055)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--noise-multipliers", type=str, default="0,0.01,0.02,0.05,0.1")
    parser.add_argument("--delta", type=float, default=1e-5)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    noise_values = [float(value.strip()) for value in args.noise_multipliers.split(",") if value.strip()]

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
    for index, noise_multiplier in enumerate(noise_values):
        model, _, _ = run_federated_training(
            train.x,
            train.y,
            train.banks,
            test.x,
            test.y,
            test.banks,
            FederatedConfig(
                rounds=args.rounds,
                local_epochs=args.local_epochs,
                dp_enabled=noise_multiplier > 0,
                noise_multiplier=noise_multiplier,
                seed=args.seed + index,
            ),
        )
        train_scores = predict_scores(model, train.x)
        threshold, _ = best_f1_threshold(train.y, train_scores)
        test_scores = predict_scores(model, test.x)
        metrics = classification_metrics(test.y, test_scores, threshold=threshold)
        privacy = estimate_gaussian_epsilon(
            noise_multiplier=noise_multiplier,
            sampling_rate=1.0,
            steps=args.rounds * len(set(train.banks)),
            delta=args.delta,
        )
        rows.append(
            {
                "noise_multiplier": noise_multiplier,
                "epsilon": privacy.epsilon,
                "delta": privacy.delta,
                "rounds": args.rounds,
                "local_epochs": args.local_epochs,
                **metrics,
                "privacy_note": privacy.note,
            }
        )

    sweep = pd.DataFrame(rows)
    sweep.to_csv(args.output_dir / "dp_sweep.csv", index=False)
    _write_privacy_report(args.output_dir, sweep)
    best = sweep.sort_values(["f1", "epsilon"], ascending=[False, True]).iloc[0]
    print(
        "Best DP sweep row: "
        f"noise={best['noise_multiplier']:.3f}, epsilon={best['epsilon']:.3f}, "
        f"f1={best['f1']:.3f}, roc_auc={best['roc_auc']:.3f}"
    )
    print(f"DP sweep written to {(args.output_dir / 'dp_sweep.csv').resolve()}")


def _write_privacy_report(output_dir: Path, sweep: pd.DataFrame) -> None:
    report = [
        "# DP Sweep Report",
        "",
        "This report uses the local demo accountant in `sentinel_fds.privacy.dp`.",
        "It is useful for comparing privacy/performance trends, not for formal DP claims.",
        "",
        "```text",
        sweep.to_string(index=False),
        "```",
    ]
    (output_dir / "privacy_report.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
