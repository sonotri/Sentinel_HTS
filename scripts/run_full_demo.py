from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Sentinel demo workflow end to end.")
    parser.add_argument("--quick", action="store_true", help="Use small datasets for a fast local smoke run.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.quick:
        commands = [
            ["python3", "scripts/run_experiment.py", "--config", "configs/default.yaml", "--rounds", "2", "--samples-per-bank", "250", "--local-epochs", "1", "--centralized-epochs", "2"],
            ["python3", "scripts/predict_with_artifact.py"],
            ["python3", "scripts/run_dp_sweep.py", "--rounds", "2", "--samples-per-bank", "250", "--local-epochs", "1", "--noise-multipliers", "0,0.02,0.05"],
            ["python3", "scripts/run_opacus_dp.py", "--samples-per-bank", "120", "--epochs", "1", "--noise-multiplier", "1.0"],
            ["python3", "scripts/run_poisoning_attack.py", "--rounds", "2", "--samples-per-bank", "250", "--local-epochs", "1"],
            ["python3", "scripts/run_gradient_leakage.py", "--iterations", "40", "--samples-per-bank", "200"],
            ["python3", "scripts/run_secure_aggregation.py", "--rounds", "2", "--samples-per-bank", "200", "--local-epochs", "1"],
            ["python3", "scripts/run_streaming_simulation.py", "--mode", "file", "--samples-per-bank", "5"],
            ["python3", "scripts/generate_final_report.py"],
        ]
    else:
        commands = [
            ["python3", "scripts/run_experiment.py", "--config", "configs/default.yaml"],
            ["python3", "scripts/predict_with_artifact.py"],
            ["python3", "scripts/run_dp_sweep.py"],
            ["python3", "scripts/run_opacus_dp.py"],
            ["python3", "scripts/run_poisoning_attack.py"],
            ["python3", "scripts/run_gradient_leakage.py"],
            ["python3", "scripts/run_secure_aggregation.py"],
            ["python3", "scripts/run_streaming_simulation.py", "--mode", "file"],
            ["python3", "scripts/generate_final_report.py"],
        ]

    for command in commands:
        print(f"\n$ {' '.join(command)}", flush=True)
        subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
