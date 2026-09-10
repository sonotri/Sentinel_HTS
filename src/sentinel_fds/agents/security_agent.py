from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class AgentDecision:
    risk_level: str
    action: str
    reasons: list[str]

    @property
    def explanation(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "No strong anomaly signal."


class SecurityAgent:
    def decide(self, transaction: pd.Series, fraud_score: float) -> AgentDecision:
        risk_level = self._risk_level(fraud_score)
        reasons = self._investigate(transaction, fraud_score)
        action = self._response(risk_level)
        return AgentDecision(risk_level=risk_level, action=action, reasons=reasons)

    def decide_many(self, df: pd.DataFrame, scores) -> pd.DataFrame:
        rows = []
        for (_, transaction), score in zip(df.iterrows(), scores):
            decision = self.decide(transaction, float(score))
            rows.append(
                {
                    "transaction_id": transaction["transaction_id"],
                    "bank": transaction["bank"],
                    "fraud_score": round(float(score), 4),
                    "risk_level": decision.risk_level,
                    "action": decision.action,
                    "explanation": decision.explanation,
                    "is_fraud": int(transaction["is_fraud"]),
                }
            )
        return pd.DataFrame(rows)

    def _risk_level(self, fraud_score: float) -> str:
        if fraud_score >= 0.9:
            return "CRITICAL"
        if fraud_score >= 0.72:
            return "HIGH"
        if fraud_score >= 0.45:
            return "MEDIUM"
        return "LOW"

    def _response(self, risk_level: str) -> str:
        return {
            "LOW": "APPROVE",
            "MEDIUM": "REQUIRE_OTP",
            "HIGH": "BLOCK_TRANSACTION",
            "CRITICAL": "LOCK_ACCOUNT",
        }[risk_level]

    def _investigate(self, transaction: pd.Series, fraud_score: float) -> list[str]:
        reasons = [f"fraud score {fraud_score:.2f}"]
        if transaction["device_new"] == 1:
            reasons.append("new device observed")
        if transaction["country"] != "KR":
            reasons.append(f"foreign country {transaction['country']}")
        if int(transaction["hour"]) <= 4 or int(transaction["hour"]) >= 23:
            reasons.append(f"unusual transaction hour {int(transaction['hour']):02d}:00")
        if float(transaction["ip_risk"]) >= 0.65:
            reasons.append(f"high IP risk {float(transaction['ip_risk']):.2f}")
        if int(transaction["velocity"]) >= 5:
            reasons.append(f"high short-window velocity {int(transaction['velocity'])}")
        if float(transaction["amount"]) >= 500:
            reasons.append(f"large amount {float(transaction['amount']):.2f}")
        if transaction["merchant"] in {"crypto", "travel", "electronics"}:
            reasons.append(f"risk-sensitive merchant {transaction['merchant']}")
        return reasons
