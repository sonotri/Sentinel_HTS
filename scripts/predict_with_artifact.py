from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_fds.models.artifacts import load_fds_artifact, score_transactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score transactions with a saved Sentinel FDS artifact.")
    parser.add_argument("--artifact-dir", type=Path, default=Path("outputs/artifacts"))
    parser.add_argument("--input", type=Path, default=Path("outputs/test_transactions.csv"))
    parser.add_argument("--output", type=Path, default=Path("outputs/predictions.csv"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact = load_fds_artifact(args.artifact_dir)
    transactions = pd.read_csv(args.input)
    predictions = score_transactions(artifact, transactions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(args.output, index=False)
    print(f"Scored {len(predictions)} transactions with threshold={artifact.threshold:.4f}")
    print(f"Predictions written to {args.output.resolve()}")


if __name__ == "__main__":
    main()
