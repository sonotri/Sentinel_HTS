from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import torch

from sentinel_fds.agents.security_agent import SecurityAgent
from sentinel_fds.models.fds import FraudMLP, predict_scores
from sentinel_fds.models.preprocessing import FEATURE_COLUMNS


@dataclass(frozen=True)
class FDSArtifact:
    model: FraudMLP
    transformer: object
    threshold: float
    metadata: dict


def save_fds_artifact(
    artifact_dir: Path,
    model: FraudMLP,
    transformer: object,
    threshold: float,
    metadata: dict,
) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "input_dim": next(model.parameters()).shape[1],
        },
        artifact_dir / "fds_model.pt",
    )
    with (artifact_dir / "preprocessor.pkl").open("wb") as file:
        pickle.dump(transformer, file)
    manifest = {
        "threshold": threshold,
        "feature_columns": FEATURE_COLUMNS,
        **metadata,
    }
    (artifact_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_fds_artifact(artifact_dir: Path) -> FDSArtifact:
    manifest = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))
    checkpoint = torch.load(artifact_dir / "fds_model.pt", map_location="cpu")
    model = FraudMLP(input_dim=int(checkpoint["input_dim"]))
    model.load_state_dict(checkpoint["state_dict"])
    with (artifact_dir / "preprocessor.pkl").open("rb") as file:
        transformer = pickle.load(file)
    return FDSArtifact(
        model=model,
        transformer=transformer,
        threshold=float(manifest["threshold"]),
        metadata=manifest,
    )


def score_transactions(artifact: FDSArtifact, transactions: pd.DataFrame) -> pd.DataFrame:
    features = artifact.transformer.transform(transactions[FEATURE_COLUMNS])
    scores = predict_scores(artifact.model, features)
    rows = []
    agent = SecurityAgent()
    for (_, transaction), score in zip(transactions.reset_index(drop=True).iterrows(), scores):
        decision = agent.decide(transaction, float(score))
        row = {
            "transaction_id": transaction.get("transaction_id", ""),
            "bank": transaction.get("bank", ""),
            "fraud_score": round(float(score), 4),
            "predicted_fraud": int(float(score) >= artifact.threshold),
            "risk_level": decision.risk_level,
            "action": decision.action,
            "explanation": decision.explanation,
        }
        if "is_fraud" in transaction:
            row["is_fraud"] = int(transaction["is_fraud"])
        rows.append(row)
    return pd.DataFrame(rows)
