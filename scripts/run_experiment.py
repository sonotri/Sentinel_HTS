from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_fds.agents.security_agent import SecurityAgent
from sentinel_fds.config import ExperimentConfig, load_experiment_config, merge_config
from sentinel_fds.evaluation.metrics import best_f1_threshold, classification_metrics, threshold_curve
from sentinel_fds.fl.fedavg import FederatedConfig, run_federated_training
from sentinel_fds.models.artifacts import save_fds_artifact
from sentinel_fds.models.baselines import train_centralized_baseline, train_local_only_baseline
from sentinel_fds.models.fds import predict_scores
from sentinel_fds.models.preprocessing import fit_transform_transactions, transform_transactions
from sentinel_fds.simulation.transactions import SimulationConfig, generate_transactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Sentinel federated FDS experiment.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--samples-per-bank", type=int, default=None)
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--local-epochs", type=int, default=None)
    parser.add_argument("--centralized-epochs", type=int, default=None)
    parser.add_argument("--fraud-rate", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--disable-dp", action="store_true")
    parser.add_argument("--noise-multiplier", type=float, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--no-save-artifacts", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = _build_config(args)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    transactions = generate_transactions(
        SimulationConfig(
            samples_per_bank=config.samples_per_bank,
            fraud_rate=config.fraud_rate,
            seed=config.seed,
        )
    )
    train_df, test_df = train_test_split(
        transactions,
        test_size=0.25,
        random_state=config.seed,
        stratify=transactions["is_fraud"],
    )

    train = fit_transform_transactions(train_df)
    test = transform_transactions(test_df, train.transformer)
    fl_model, round_metrics, fl_bank_metrics = run_federated_training(
        train.x,
        train.y,
        train.banks,
        test.x,
        test.y,
        test.banks,
        FederatedConfig(
            rounds=config.rounds,
            local_epochs=config.local_epochs,
            dp_enabled=config.dp_enabled,
            noise_multiplier=config.noise_multiplier,
            seed=config.seed,
        ),
    )

    fl_train_scores = predict_scores(fl_model, train.x)
    tuned_threshold, tuned_train_metrics = best_f1_threshold(train.y, fl_train_scores)
    scores = predict_scores(fl_model, test.x)
    tuned_fl_metrics = classification_metrics(test.y, scores, threshold=tuned_threshold)
    fl_bank_metrics = _bank_metrics("Federated", test.y, scores, test.banks, tuned_threshold)

    centralized_model, centralized_metrics = train_centralized_baseline(
        train.x,
        train.y,
        test.x,
        test.y,
        epochs=config.centralized_epochs,
        batch_size=128,
        lr=1e-3,
        seed=config.seed,
    )
    centralized_scores = predict_scores(centralized_model, test.x)
    centralized_threshold = centralized_metrics["threshold"]
    centralized_bank_metrics = _bank_metrics(
        "Centralized oracle",
        test.y,
        centralized_scores,
        test.banks,
        centralized_threshold,
    )

    local_metrics, local_bank_metrics = train_local_only_baseline(
        train.x,
        train.y,
        train.banks,
        test.x,
        test.y,
        test.banks,
        epochs=max(config.rounds * config.local_epochs, 1),
        batch_size=128,
        lr=1e-3,
        seed=config.seed,
    )

    comparison = pd.DataFrame(
        [
            {"model": "Local-only", **local_metrics},
            {"model": "Federated", **tuned_fl_metrics},
            {"model": "Centralized oracle", **centralized_metrics},
        ]
    )
    bank_comparison = pd.concat(
        [local_bank_metrics, fl_bank_metrics, centralized_bank_metrics],
        ignore_index=True,
    )
    threshold_df = pd.DataFrame(threshold_curve(train.y, fl_train_scores))
    threshold_df.insert(0, "model", "Federated")

    decision_df = SecurityAgent().decide_many(test_df.reset_index(drop=True), scores)
    sample_decisions = decision_df.sort_values("fraud_score", ascending=False).head(150)

    transactions.to_csv(config.output_dir / "transactions.csv", index=False)
    test_df.to_csv(config.output_dir / "test_transactions.csv", index=False)
    round_metrics.to_csv(config.output_dir / "metrics.csv", index=False)
    fl_bank_metrics.to_csv(config.output_dir / "bank_metrics.csv", index=False)
    comparison.to_csv(config.output_dir / "model_comparison.csv", index=False)
    bank_comparison.to_csv(config.output_dir / "bank_model_comparison.csv", index=False)
    threshold_df.to_csv(config.output_dir / "threshold_curve.csv", index=False)
    sample_decisions.to_csv(config.output_dir / "sample_decisions.csv", index=False)
    if config.save_artifacts:
        save_fds_artifact(
            config.output_dir / "artifacts",
            fl_model,
            train.transformer,
            tuned_threshold,
            {
                "model_type": "Federated FraudMLP",
                "input_dim": int(train.x.shape[1]),
                "feature_names": train.feature_names,
                "rounds": config.rounds,
                "local_epochs": config.local_epochs,
                "dp_enabled": config.dp_enabled,
                "noise_multiplier": config.noise_multiplier,
                "seed": config.seed,
            },
        )
    _write_summary(
        config.output_dir,
        round_metrics,
        comparison,
        bank_comparison,
        sample_decisions,
        config,
        tuned_train_metrics,
    )

    final = tuned_fl_metrics
    print(
        "Final tuned federated metrics: "
        f"precision={final['precision']:.3f}, recall={final['recall']:.3f}, "
        f"f1={final['f1']:.3f}, roc_auc={final['roc_auc']:.3f}, "
        f"threshold={final['threshold']:.3f}"
    )
    print(f"Artifacts written to {config.output_dir.resolve()}")


def _build_config(args: argparse.Namespace) -> ExperimentConfig:
    base = load_experiment_config(args.config)
    overrides = {
        "samples_per_bank": args.samples_per_bank,
        "rounds": args.rounds,
        "local_epochs": args.local_epochs,
        "centralized_epochs": args.centralized_epochs,
        "fraud_rate": args.fraud_rate,
        "seed": args.seed,
        "noise_multiplier": args.noise_multiplier,
        "output_dir": args.output_dir,
    }
    if args.disable_dp:
        overrides["dp_enabled"] = False
    if args.no_save_artifacts:
        overrides["save_artifacts"] = False
    return merge_config(base, overrides)


def _bank_metrics(
    model_name: str,
    y_true,
    scores,
    banks,
    threshold: float,
) -> pd.DataFrame:
    rows = []
    for bank in sorted(set(banks)):
        mask = banks == bank
        rows.append(
            {
                "model": model_name,
                "bank": bank,
                **classification_metrics(y_true[mask], scores[mask], threshold=threshold),
                "samples": int(mask.sum()),
            }
        )
    return pd.DataFrame(rows)


def _write_summary(
    output_dir: Path,
    round_metrics: pd.DataFrame,
    model_comparison: pd.DataFrame,
    bank_model_comparison: pd.DataFrame,
    decisions: pd.DataFrame,
    config: ExperimentConfig,
    tuned_train_metrics: dict[str, float],
) -> None:
    final = model_comparison[model_comparison["model"] == "Federated"].iloc[0]
    critical = int((decisions["risk_level"] == "CRITICAL").sum())
    high = int((decisions["risk_level"] == "HIGH").sum())
    summary = [
        "# Sentinel Experiment Summary",
        "",
        f"- samples_per_bank: {config.samples_per_bank}",
        f"- rounds: {config.rounds}",
        f"- local_epochs: {config.local_epochs}",
        f"- centralized_epochs: {config.centralized_epochs}",
        f"- dp_enabled: {config.dp_enabled}",
        f"- noise_multiplier: {config.noise_multiplier}",
        f"- save_artifacts: {config.save_artifacts}",
        "",
        "## Tuned Federated Metrics",
        "",
        f"- precision: {final['precision']:.4f}",
        f"- recall: {final['recall']:.4f}",
        f"- f1: {final['f1']:.4f}",
        f"- roc_auc: {final['roc_auc']:.4f}",
        f"- threshold: {final['threshold']:.4f}",
        f"- train_f1_at_threshold: {tuned_train_metrics['f1']:.4f}",
        "",
        "## Model Comparison",
        "",
        "```text",
        model_comparison.to_string(index=False),
        "```",
        "",
        "## Agent Decisions In Top 150 Scores",
        "",
        f"- critical: {critical}",
        f"- high: {high}",
        "",
        "## Bank/Model Metrics",
        "",
        "```text",
        bank_model_comparison.to_string(index=False),
        "```",
        "",
        "## Federated Round Metrics",
        "",
        "```text",
        round_metrics.to_string(index=False),
        "```",
    ]
    (output_dir / "summary.md").write_text("\n".join(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
