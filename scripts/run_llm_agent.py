from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_fds.agents.llm_agent import generate_llm_fraud_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an LLM fraud analyst report from sample decisions.")
    parser.add_argument("--input", type=Path, default=Path("outputs/sample_decisions.csv"))
    parser.add_argument("--output", type=Path, default=Path("outputs/llm_fraud_report.md"))
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--limit", type=int, default=25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    decisions = pd.read_csv(args.input).head(args.limit)
    report = generate_llm_fraud_report(decisions.to_json(orient="records"), model=args.model)
    args.output.write_text(report, encoding="utf-8")
    print(f"LLM fraud report written to {args.output.resolve()}")


if __name__ == "__main__":
    main()
