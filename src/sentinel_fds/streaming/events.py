from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable

import pandas as pd


def transaction_events(transactions: pd.DataFrame) -> Iterable[dict]:
    for row in transactions.to_dict(orient="records"):
        yield row


def write_jsonl_stream(events: Iterable[dict], output: Path, delay_seconds: float = 0.0) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as file:
        for event in events:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")
            count += 1
            if delay_seconds > 0:
                time.sleep(delay_seconds)
    return count


def publish_kafka_events(
    events: Iterable[dict],
    bootstrap_servers: str,
    topic: str,
    delay_seconds: float = 0.0,
) -> int:
    from kafka import KafkaProducer

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )
    count = 0
    for event in events:
        producer.send(topic, event)
        count += 1
        if delay_seconds > 0:
            time.sleep(delay_seconds)
    producer.flush()
    producer.close()
    return count
