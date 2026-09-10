from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_fds.models.artifacts import load_fds_artifact
from sentinel_fds.models.fds import FraudMLP, train_local_model
from sentinel_fds.models.preprocessing import fit_transform_transactions, transform_transactions
from sentinel_fds.privacy.leakage import gradient_leakage_attack
from sentinel_fds.simulation.transactions import SimulationConfig, generate_transactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a gradient leakage reconstruction attack.")
    parser.add_argument("--artifact-dir", type=Path, default=Path("outputs/artifacts"))
    parser.add_argument("--samples-per-bank", type=int, default=500)
    parser.add_argument("--iterations", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-index", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model, prepared, feature_names, source = _load_or_train_target(args)
    target_index = min(max(args.target_index, 0), len(prepared.y) - 1)
    result = gradient_leakage_attack(
        model,
        prepared.x[target_index],
        float(prepared.y[target_index]),
        iterations=args.iterations,
        seed=args.seed,
    )

    summary = pd.DataFrame(
        [
            {
                "source": source,
                "target_index": target_index,
                "iterations": args.iterations,
                "feature_mse": result.feature_mse,
                "feature_mae": result.feature_mae,
                "label_abs_error": result.label_abs_error,
                "gradient_mse": result.gradient_mse,
                "true_label": result.true_label,
                "reconstructed_label": result.reconstructed_label,
                "true_score": result.true_score,
                "reconstructed_score": result.reconstructed_score,
            }
        ]
    )
    feature_rows = pd.DataFrame(
        {
            "feature": feature_names,
            "true_value": prepared.x[target_index],
            "reconstructed_value": result.reconstructed_features,
            "absolute_error": abs(result.reconstructed_features - prepared.x[target_index]),
        }
    ).sort_values("absolute_error", ascending=False)
    summary.to_csv(args.output_dir / "gradient_leakage.csv", index=False)
    feature_rows.to_csv(args.output_dir / "gradient_leakage_features.csv", index=False)
    _write_report(args.output_dir, summary, feature_rows.head(15))
    print(
        "Gradient leakage result: "
        f"feature_mae={result.feature_mae:.4f}, label_abs_error={result.label_abs_error:.4f}, "
        f"gradient_mse={result.gradient_mse:.6f}"
    )
    print(f"Leakage report written to {(args.output_dir / 'gradient_leakage.csv').resolve()}")


def _load_or_train_target(args: argparse.Namespace):
    transactions = generate_transactions(SimulationConfig(samples_per_bank=args.samples_per_bank, seed=args.seed))
    train_df, test_df = train_test_split(
        transactions,
        test_size=0.25,
        random_state=args.seed,
        stratify=transactions["is_fraud"],
    )
    if args.artifact_dir.exists():
        artifact = load_fds_artifact(args.artifact_dir)
        prepared = transform_transactions(test_df, artifact.transformer)
        feature_names = artifact.metadata.get("feature_names", [f"feature_{i}" for i in range(prepared.x.shape[1])])
        return artifact.model, prepared, feature_names, "saved_artifact"

    prepared_train = fit_transform_transactions(train_df)
    prepared_test = transform_transactions(test_df, prepared_train.transformer)
    model = FraudMLP(input_dim=prepared_train.x.shape[1])
    train_local_model(model, prepared_train.x, prepared_train.y, epochs=2)
    return model, prepared_test, prepared_train.feature_names, "scratch_model"


def _write_report(output_dir: Path, summary: pd.DataFrame, feature_rows: pd.DataFrame) -> None:
    report = [
        "# Gradient Leakage Attack Report",
        "",
        "This is a DLG-style reconstruction demo against a single transaction gradient.",
        "Lower feature/label error means more leakage.",
        "",
        "## Summary",
        "",
        "```text",
        summary.to_string(index=False),
        "```",
        "",
        "## Largest Feature Errors",
        "",
        "```text",
        feature_rows.to_string(index=False),
        "```",
    ]
    (output_dir / "gradient_leakage_report.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
