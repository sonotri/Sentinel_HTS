from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


BANK_PROFILES = {
    "Bank A": {
        "amount_mu": 4.4,
        "amount_sigma": 0.65,
        "foreign_rate": 0.04,
        "new_device_rate": 0.06,
        "ip_risk_alpha": (1.2, 9.0),
        "merchant_probs": {
            "convenience": 0.27,
            "cafe": 0.23,
            "grocery": 0.22,
            "subscription": 0.14,
            "electronics": 0.08,
            "travel": 0.04,
            "crypto": 0.02,
        },
    },
    "Bank B": {
        "amount_mu": 4.9,
        "amount_sigma": 0.9,
        "foreign_rate": 0.28,
        "new_device_rate": 0.1,
        "ip_risk_alpha": (1.8, 6.5),
        "merchant_probs": {
            "convenience": 0.11,
            "cafe": 0.13,
            "grocery": 0.12,
            "subscription": 0.12,
            "electronics": 0.16,
            "travel": 0.27,
            "crypto": 0.09,
        },
    },
    "Bank C": {
        "amount_mu": 3.45,
        "amount_sigma": 0.55,
        "foreign_rate": 0.02,
        "new_device_rate": 0.08,
        "ip_risk_alpha": (1.0, 10.0),
        "merchant_probs": {
            "convenience": 0.31,
            "cafe": 0.3,
            "grocery": 0.16,
            "subscription": 0.11,
            "electronics": 0.06,
            "travel": 0.02,
            "crypto": 0.04,
        },
    },
}

COUNTRIES = ["KR", "US", "JP", "CN", "VN", "GB", "DE", "RU"]
MERCHANTS = [
    "convenience",
    "cafe",
    "grocery",
    "subscription",
    "electronics",
    "travel",
    "crypto",
]


@dataclass(frozen=True)
class SimulationConfig:
    samples_per_bank: int = 3000
    fraud_rate: float = 0.055
    seed: int = 42


def generate_transactions(config: SimulationConfig) -> pd.DataFrame:
    frames = []
    rng = np.random.default_rng(config.seed)
    for bank_name, profile in BANK_PROFILES.items():
        frames.append(_generate_bank_transactions(bank_name, profile, config, rng))

    df = pd.concat(frames, ignore_index=True)
    df.insert(0, "transaction_id", [f"tx_{i:07d}" for i in range(len(df))])
    return df


def _generate_bank_transactions(
    bank_name: str,
    profile: dict,
    config: SimulationConfig,
    rng: np.random.Generator,
) -> pd.DataFrame:
    n = config.samples_per_bank
    fraud = rng.binomial(1, config.fraud_rate, size=n)

    amount = rng.lognormal(profile["amount_mu"], profile["amount_sigma"], size=n)
    hour = _normal_hours(rng, n)
    foreign = rng.binomial(1, profile["foreign_rate"], size=n)
    country = np.where(foreign == 1, rng.choice(COUNTRIES[1:], size=n), "KR")
    device_new = rng.binomial(1, profile["new_device_rate"], size=n)
    alpha, beta = profile["ip_risk_alpha"]
    ip_risk = rng.beta(alpha, beta, size=n)
    velocity = rng.poisson(1.35, size=n)

    merchant_names = list(profile["merchant_probs"].keys())
    merchant_probs = list(profile["merchant_probs"].values())
    merchant = rng.choice(merchant_names, p=merchant_probs, size=n)

    fraud_idx = fraud == 1
    amount[fraud_idx] *= rng.lognormal(1.45, 0.55, size=fraud_idx.sum())
    hour[fraud_idx] = rng.choice([0, 1, 2, 3, 4, 23], size=fraud_idx.sum())
    country[fraud_idx] = rng.choice(COUNTRIES[1:], size=fraud_idx.sum())
    device_new[fraud_idx] = rng.binomial(1, 0.72, size=fraud_idx.sum())
    ip_risk[fraud_idx] = np.maximum(ip_risk[fraud_idx], rng.beta(5.2, 1.8, size=fraud_idx.sum()))
    velocity[fraud_idx] += rng.poisson(4.0, size=fraud_idx.sum())
    merchant[fraud_idx] = rng.choice(
        ["electronics", "travel", "crypto"],
        p=[0.38, 0.27, 0.35],
        size=fraud_idx.sum(),
    )

    return pd.DataFrame(
        {
            "bank": bank_name,
            "amount": amount.round(2),
            "country": country,
            "merchant": merchant,
            "hour": hour,
            "device_new": device_new,
            "ip_risk": ip_risk.round(4),
            "velocity": velocity,
            "is_fraud": fraud,
        }
    )


def _normal_hours(rng: np.random.Generator, n: int) -> np.ndarray:
    daytime = rng.normal(14, 4, size=n).round().astype(int)
    evening = rng.normal(20, 2, size=n).round().astype(int)
    use_evening = rng.binomial(1, 0.28, size=n).astype(bool)
    hours = np.where(use_evening, evening, daytime)
    return np.clip(hours, 0, 23)
