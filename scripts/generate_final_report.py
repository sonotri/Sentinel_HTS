from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a consolidated Sentinel experiment report.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--report", type=Path, default=Path("outputs/final_report.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.output_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    print(f"Final report written to {args.report.resolve()}")


def build_report(output_dir: Path) -> str:
    sections = [
        "# Sentinel Final Report",
        "",
        "Privacy-preserving federated fraud detection experiment for virtual banks.",
        "",
    ]
    sections += _model_summary(output_dir)
    sections += _dp_summary(output_dir)
    sections += _security_summary(output_dir)
    sections += _runtime_summary(output_dir)
    sections += _artifact_summary(output_dir)
    return "\n".join(sections)


def _model_summary(output_dir: Path) -> list[str]:
    comparison = _read_optional(output_dir / "model_comparison.csv")
    bank_comparison = _read_optional(output_dir / "bank_model_comparison.csv")
    if comparison is None:
        return ["## Model Comparison", "", "Run `python3 scripts/run_experiment.py --config configs/default.yaml`.", ""]

    federated = comparison[comparison["model"] == "Federated"].iloc[0]
    lines = [
        "## Model Comparison",
        "",
        f"- Federated F1: {federated['f1']:.4f}",
        f"- Federated ROC-AUC: {federated['roc_auc']:.4f}",
        f"- Tuned threshold: {federated['threshold']:.4f}",
        "",
        "```text",
        comparison.to_string(index=False),
        "```",
        "",
    ]
    if bank_comparison is not None:
        lines += [
            "### Bank/Model Breakdown",
            "",
            "```text",
            bank_comparison.to_string(index=False),
            "```",
            "",
        ]
    return lines


def _dp_summary(output_dir: Path) -> list[str]:
    dp_sweep = _read_optional(output_dir / "dp_sweep.csv")
    opacus = _read_optional(output_dir / "opacus_dp.csv")
    secure = _read_optional(output_dir / "secure_aggregation.csv")
    lines = ["## Privacy", ""]
    if dp_sweep is not None:
        lines += [
            "### DP Noise Sweep",
            "",
            "```text",
            dp_sweep.to_string(index=False),
            "```",
            "",
        ]
    if opacus is not None:
        row = opacus.iloc[0]
        lines += [
            "### Opacus DP-SGD",
            "",
            f"- Epsilon: {row['epsilon']:.4f}",
            f"- Delta: {row['delta']:.0e}",
            f"- F1: {row['f1']:.4f}",
            "",
        ]
    if secure is not None:
        lines += [
            "### Secure Aggregation",
            "",
            "```text",
            secure.to_string(index=False),
            "```",
            "",
        ]
    if len(lines) == 2:
        lines.append("Run DP and secure aggregation scripts to populate this section.\n")
    return lines


def _security_summary(output_dir: Path) -> list[str]:
    poisoning = _read_optional(output_dir / "poisoning_attack.csv")
    leakage = _read_optional(output_dir / "gradient_leakage.csv")
    lines = ["## Security Experiments", ""]
    if poisoning is not None:
        clean = poisoning[poisoning["scenario"] == "clean"].iloc[0]
        worst = poisoning.sort_values("f1").iloc[0]
        lines += [
            "### Model Poisoning",
            "",
            f"- Clean F1: {clean['f1']:.4f}",
            f"- Worst scenario: {worst['scenario']} ({worst['attack']})",
            f"- Worst F1: {worst['f1']:.4f}",
            f"- F1 delta: {worst['f1'] - clean['f1']:.4f}",
            "",
            "```text",
            poisoning.to_string(index=False),
            "```",
            "",
        ]
    if leakage is not None:
        row = leakage.iloc[0]
        lines += [
            "### Gradient Leakage",
            "",
            f"- Feature MAE: {row['feature_mae']:.4f}",
            f"- Label absolute error: {row['label_abs_error']:.4f}",
            f"- Gradient MSE: {row['gradient_mse']:.6f}",
            "",
        ]
    if len(lines) == 2:
        lines.append("Run poisoning and leakage scripts to populate this section.\n")
    return lines


def _runtime_summary(output_dir: Path) -> list[str]:
    stream = output_dir / "transaction_stream.jsonl"
    flower = _read_optional(output_dir / "flower_history.csv")
    lines = ["## Runtime Integrations", ""]
    if stream.exists():
        event_count = sum(1 for _ in stream.open("r", encoding="utf-8"))
        lines.append(f"- Transaction stream events: {event_count}")
    if flower is not None:
        lines.append("- Flower simulation: executed")
    if (output_dir / "llm_fraud_report.md").exists():
        lines.append("- LLM fraud report: generated")
    if len(lines) == 2:
        lines.append("- Runtime integration outputs not generated yet.")
    lines.append("")
    return lines


def _artifact_summary(output_dir: Path) -> list[str]:
    artifact_dir = output_dir / "artifacts"
    artifact_files = sorted(path.name for path in artifact_dir.glob("*")) if artifact_dir.exists() else []
    lines = [
        "## Reproducibility Artifacts",
        "",
        f"- Output directory: `{output_dir}`",
    ]
    if artifact_files:
        lines.append(f"- Saved model artifacts: {', '.join(artifact_files)}")
    lines += [
        "",
        "## Recommended Demo Order",
        "",
        "1. Run `python3 scripts/run_full_demo.py --quick`.",
        "2. Open `streamlit run dashboard/app.py`.",
        "3. Present `outputs/final_report.md` as the experiment summary.",
        "",
    ]
    return lines


def _read_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


if __name__ == "__main__":
    main()
