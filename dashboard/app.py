from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


OUTPUT_DIR = Path("outputs")


st.set_page_config(page_title="Sentinel Federated FDS", layout="wide")
st.title("Sentinel Federated FDS")


def load_csv(name: str) -> pd.DataFrame:
    path = OUTPUT_DIR / name
    if not path.exists():
        st.warning("Run `python scripts/run_experiment.py` first.")
        st.stop()
    return pd.read_csv(path)


def optional_csv(name: str) -> pd.DataFrame | None:
    path = OUTPUT_DIR / name
    if not path.exists():
        return None
    return pd.read_csv(path)


metrics = load_csv("metrics.csv")
model_comparison = load_csv("model_comparison.csv")
bank_model_comparison = load_csv("bank_model_comparison.csv")
threshold_curve = load_csv("threshold_curve.csv")
transactions = load_csv("transactions.csv")
decisions = load_csv("sample_decisions.csv")
dp_sweep = optional_csv("dp_sweep.csv")
poisoning_attack = optional_csv("poisoning_attack.csv")
poisoning_attack_by_bank = optional_csv("poisoning_attack_by_bank.csv")
gradient_leakage = optional_csv("gradient_leakage.csv")
gradient_leakage_features = optional_csv("gradient_leakage_features.csv")
secure_aggregation = optional_csv("secure_aggregation.csv")
secure_aggregation_rounds = optional_csv("secure_aggregation_rounds.csv")
opacus_dp = optional_csv("opacus_dp.csv")
final_report_path = OUTPUT_DIR / "final_report.md"

latest = model_comparison[model_comparison["model"] == "Federated"].iloc[0]
cols = st.columns(4)
cols[0].metric("Precision", f"{latest['precision']:.3f}")
cols[1].metric("Recall", f"{latest['recall']:.3f}")
cols[2].metric("F1", f"{latest['f1']:.3f}")
cols[3].metric("ROC-AUC", f"{latest['roc_auc']:.3f}")

if final_report_path.exists():
    with st.expander("Final Report", expanded=False):
        st.markdown(final_report_path.read_text(encoding="utf-8"))
else:
    st.info("Run `python3 scripts/generate_final_report.py` to create the consolidated Markdown report.")

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Model Comparison")
    compare_metric = st.selectbox("Comparison metric", ["precision", "recall", "f1", "roc_auc"], index=2)
    st.plotly_chart(
        px.bar(
            model_comparison,
            x="model",
            y=compare_metric,
            color="model",
            text_auto=".3f",
        ),
        use_container_width=True,
    )

with right:
    st.subheader("Threshold Tuning")
    st.plotly_chart(
        px.line(threshold_curve, x="threshold", y=["precision", "recall", "f1"]),
        use_container_width=True,
    )

st.subheader("DP Privacy/Performance Sweep")
if dp_sweep is None:
    st.info("Run `python3 scripts/run_dp_sweep.py` to generate DP sweep results.")
else:
    dp_cols = st.columns([1.1, 1])
    with dp_cols[0]:
        dp_metric = st.selectbox("DP metric", ["f1", "precision", "recall", "roc_auc"], index=0)
        st.plotly_chart(
            px.line(
                dp_sweep,
                x="noise_multiplier",
                y=dp_metric,
                markers=True,
                hover_data=["epsilon", "threshold"],
            ),
            use_container_width=True,
        )
    with dp_cols[1]:
        finite = dp_sweep[dp_sweep["epsilon"] != float("inf")].copy()
        if finite.empty:
            st.dataframe(dp_sweep, use_container_width=True, hide_index=True)
        else:
            st.plotly_chart(
                px.scatter(
                    finite,
                    x="epsilon",
                    y="f1",
                    color="noise_multiplier",
                    size="roc_auc",
                    hover_data=["precision", "recall"],
                ),
                use_container_width=True,
            )

st.subheader("Model Poisoning Attack")
if poisoning_attack is None:
    st.info("Run `python3 scripts/run_poisoning_attack.py` to generate poisoning attack results.")
else:
    attack_cols = st.columns([1.1, 1])
    with attack_cols[0]:
        attack_metric = st.selectbox("Attack metric", ["f1", "precision", "recall", "roc_auc"], index=0)
        st.plotly_chart(
            px.bar(
                poisoning_attack,
                x="scenario",
                y=attack_metric,
                color="attack",
                text_auto=".3f",
                hover_data=["malicious_banks", "threshold"],
            ),
            use_container_width=True,
        )
    with attack_cols[1]:
        if poisoning_attack_by_bank is None:
            st.dataframe(poisoning_attack, use_container_width=True, hide_index=True)
        else:
            st.plotly_chart(
                px.bar(
                    poisoning_attack_by_bank,
                    x="bank",
                    y="f1",
                    color="scenario",
                    barmode="group",
                    text_auto=".3f",
                ),
                use_container_width=True,
            )

st.subheader("Gradient Leakage Attack")
if gradient_leakage is None:
    st.info("Run `python3 scripts/run_gradient_leakage.py` to generate leakage reconstruction results.")
else:
    leakage = gradient_leakage.iloc[0]
    leak_cols = st.columns(4)
    leak_cols[0].metric("Feature MAE", f"{leakage['feature_mae']:.3f}")
    leak_cols[1].metric("Feature MSE", f"{leakage['feature_mse']:.3f}")
    leak_cols[2].metric("Label Error", f"{leakage['label_abs_error']:.3f}")
    leak_cols[3].metric("Gradient MSE", f"{leakage['gradient_mse']:.6f}")
    if gradient_leakage_features is not None:
        top_errors = gradient_leakage_features.sort_values("absolute_error", ascending=False).head(15)
        st.plotly_chart(
            px.bar(
                top_errors,
                x="feature",
                y="absolute_error",
                hover_data=["true_value", "reconstructed_value"],
            ),
            use_container_width=True,
            )

st.subheader("Formal DP-SGD Baseline")
if opacus_dp is None:
    st.info("Run `python3 scripts/run_opacus_dp.py` after installing Opacus to generate formal DP-SGD results.")
else:
    opacus = opacus_dp.iloc[0]
    opacus_cols = st.columns(4)
    opacus_cols[0].metric("Epsilon", f"{opacus['epsilon']:.3f}")
    opacus_cols[1].metric("Delta", f"{opacus['delta']:.0e}")
    opacus_cols[2].metric("F1", f"{opacus['f1']:.3f}")
    opacus_cols[3].metric("ROC-AUC", f"{opacus['roc_auc']:.3f}")

st.subheader("Secure Aggregation")
if secure_aggregation is None:
    st.info("Run `python3 scripts/run_secure_aggregation.py` to generate secure aggregation results.")
else:
    sec_cols = st.columns([1.1, 1])
    with sec_cols[0]:
        sec_metric = st.selectbox("Secure aggregation metric", ["f1", "precision", "recall", "roc_auc"], index=0)
        st.plotly_chart(
            px.bar(
                secure_aggregation,
                x="mode",
                y=sec_metric,
                color="mode",
                text_auto=".3f",
            ),
            use_container_width=True,
        )
    with sec_cols[1]:
        if secure_aggregation_rounds is None or "reconstruction_mse" not in secure_aggregation_rounds:
            st.dataframe(secure_aggregation, use_container_width=True, hide_index=True)
        else:
            sec_rounds = secure_aggregation_rounds[secure_aggregation_rounds["secure_aggregation"].astype(str) == "True"]
            st.plotly_chart(
                px.line(
                    sec_rounds,
                    x="round",
                    y=["reconstruction_mse", "mean_mask_delta_norm"],
                    markers=True,
                ),
                use_container_width=True,
            )

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Federated Rounds")
    round_metric = st.selectbox("Metric", ["precision", "recall", "f1", "roc_auc"], index=2)
    st.plotly_chart(
        px.line(metrics, x="round", y=round_metric, markers=True),
        use_container_width=True,
    )

with right:
    st.subheader("Bank Performance By Model")
    bank_metric = st.selectbox("Bank metric", ["precision", "recall", "f1", "roc_auc"], index=2)
    st.plotly_chart(
        px.bar(
            bank_model_comparison,
            x="bank",
            y=bank_metric,
            color="model",
            barmode="group",
            text_auto=".3f",
        ),
        use_container_width=True,
    )

st.subheader("Non-IID Transaction Distribution")
dist_cols = st.columns(2)
with dist_cols[0]:
    st.plotly_chart(
        px.box(transactions, x="bank", y="amount", color="bank", points=False),
        use_container_width=True,
    )
with dist_cols[1]:
    merchant_counts = transactions.groupby(["bank", "merchant"]).size().reset_index(name="count")
    st.plotly_chart(
        px.bar(merchant_counts, x="merchant", y="count", color="bank", barmode="group"),
        use_container_width=True,
    )

st.subheader("AI Security Agent Decisions")
risk_filter = st.multiselect(
    "Risk level",
    ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    default=["CRITICAL", "HIGH", "MEDIUM"],
)
filtered = decisions[decisions["risk_level"].isin(risk_filter)]
st.dataframe(
    filtered[
        [
            "transaction_id",
            "bank",
            "fraud_score",
            "risk_level",
            "action",
            "explanation",
            "is_fraud",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)
