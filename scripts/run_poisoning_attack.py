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
    parser = argparse.ArgumentParser(description="Run model poisoning scenarios against Sentinel FL.")
    parser.add_argument("--samples-per-bank", type=int, default=1200)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--local-epochs", type=int, default=1)
    parser.add_argument("--fraud-rate", type=float, default=0.055)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--malicious-bank", type=str, default="Bank B")
    parser.add_argument("--attack-scale", type=float, default=8.0)
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

    scenarios = [
        {"scenario": "clean", "attack": "none", "malicious_banks": ()},
        {"scenario": "label_flip", "attack": "label_flip", "malicious_banks": (args.malicious_bank,)},
        {"scenario": "update_scale", "attack": "update_scale", "malicious_banks": (args.malicious_bank,)},
    ]
    rows = []
    bank_rows = []
    for index, scenario in enumerate(scenarios):
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
                dp_enabled=not args.disable_dp,
                noise_multiplier=args.noise_multiplier,
                seed=args.seed + index,
                malicious_banks=scenario["malicious_banks"],
                attack=scenario["attack"],
                attack_scale=args.attack_scale,
            ),
        )
        train_scores = predict_scores(model, train.x)
        threshold, _ = best_f1_threshold(train.y, train_scores)
        test_scores = predict_scores(model, test.x)
        metrics = classification_metrics(test.y, test_scores, threshold=threshold)
        rows.append(
            {
                "scenario": scenario["scenario"],
                "attack": scenario["attack"],
                "malicious_banks": ",".join(scenario["malicious_banks"]),
                "attack_scale": args.attack_scale if scenario["attack"] == "update_scale" else 1.0,
                **metrics,
            }
        )
        for bank in sorted(set(test.banks)):
            mask = test.banks == bank
            bank_rows.append(
                {
                    "scenario": scenario["scenario"],
                    "bank": bank,
                    **classification_metrics(test.y[mask], test_scores[mask], threshold=threshold),
                    "samples": int(mask.sum()),
                }
            )

    attack_df = pd.DataFrame(rows)
    bank_df = pd.DataFrame(bank_rows)
    attack_df.to_csv(args.output_dir / "poisoning_attack.csv", index=False)
    bank_df.to_csv(args.output_dir / "poisoning_attack_by_bank.csv", index=False)
    _write_report(args.output_dir, attack_df, bank_df)

    clean_f1 = float(attack_df.loc[attack_df["scenario"] == "clean", "f1"].iloc[0])
    worst = attack_df.sort_values("f1").iloc[0]
    print(
        "Worst poisoning scenario: "
        f"{worst['scenario']} f1={worst['f1']:.3f}, clean_f1={clean_f1:.3f}, "
        f"delta={worst['f1'] - clean_f1:.3f}"
    )
    print(f"Poisoning results written to {(args.output_dir / 'poisoning_attack.csv').resolve()}")


def _write_report(output_dir: Path, attack_df: pd.DataFrame, bank_df: pd.DataFrame) -> None:
    report = [
        "# Model Poisoning Attack Report",
        "",
        "Scenarios compare clean FedAvg against one malicious bank.",
        "",
        "## Overall",
        "",
        "```text",
        attack_df.to_string(index=False),
        "```",
        "",
        "## By Bank",
        "",
        "```text",
        bank_df.to_string(index=False),
        "```",
    ]
    (output_dir / "poisoning_report.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
