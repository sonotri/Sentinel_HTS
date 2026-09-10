from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


FEATURE_COLUMNS = ["amount", "country", "merchant", "hour", "device_new", "ip_risk", "velocity"]
TARGET_COLUMN = "is_fraud"
NUMERIC_COLUMNS = ["amount", "hour", "device_new", "ip_risk", "velocity"]
CATEGORICAL_COLUMNS = ["country", "merchant"]


@dataclass
class PreparedData:
    x: np.ndarray
    y: np.ndarray
    transaction_ids: np.ndarray
    banks: np.ndarray
    transformer: ColumnTransformer
    feature_names: list[str]


def fit_transform_transactions(df: pd.DataFrame) -> PreparedData:
    transformer = build_transformer()
    x = transformer.fit_transform(df[FEATURE_COLUMNS])
    return _prepared(df, x, transformer)


def transform_transactions(df: pd.DataFrame, transformer: ColumnTransformer) -> PreparedData:
    x = transformer.transform(df[FEATURE_COLUMNS])
    return _prepared(df, x, transformer)


def build_transformer() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_COLUMNS),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLUMNS),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def _prepared(df: pd.DataFrame, x, transformer: ColumnTransformer) -> PreparedData:
    dense_x = np.asarray(x, dtype=np.float32)
    feature_names = list(transformer.get_feature_names_out())
    return PreparedData(
        x=dense_x,
        y=df[TARGET_COLUMN].to_numpy(dtype=np.float32),
        transaction_ids=df["transaction_id"].to_numpy(),
        banks=df["bank"].to_numpy(),
        transformer=transformer,
        feature_names=feature_names,
    )
