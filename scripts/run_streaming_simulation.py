from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_fds.simulation.transactions import SimulationConfig, generate_transactions
from sentinel_fds.streaming.events import publish_kafka_events, transaction_events, write_jsonl_stream


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream synthetic transactions to JSONL or Kafka.")
    parser.add_argument("--mode", choices=["file", "kafka"], default="file")
    parser.add_argument("--samples-per-bank", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--delay-seconds", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=Path("outputs/transaction_stream.jsonl"))
    parser.add_argument("--bootstrap-servers", type=str, default="localhost:9092")
    parser.add_argument("--topic", type=str, default="sentinel.transactions")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transactions = generate_transactions(
        SimulationConfig(samples_per_bank=args.samples_per_bank, seed=args.seed)
    )
    events = transaction_events(transactions)
    if args.mode == "file":
        count = write_jsonl_stream(events, args.output, delay_seconds=args.delay_seconds)
        print(f"Wrote {count} transaction events to {args.output.resolve()}")
    else:
        count = publish_kafka_events(
            events,
            bootstrap_servers=args.bootstrap_servers,
            topic=args.topic,
            delay_seconds=args.delay_seconds,
        )
        print(f"Published {count} transaction events to {args.topic} at {args.bootstrap_servers}")


if __name__ == "__main__":
    main()
