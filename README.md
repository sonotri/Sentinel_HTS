# Sentinel

Privacy-preserving federated fraud detection system for virtual banks.

This MVP implements:

- Synthetic transaction simulation with bank-specific non-IID distributions
- Local PyTorch FDS models
- Federated averaging across banks
- Optional DP-style update clipping and Gaussian noise
- Policy-based AI security agent for explanation and response
- Streamlit dashboard for experiment inspection

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/run_full_demo.py --quick
streamlit run dashboard/app.py
```

The experiment writes artifacts to `outputs/`:

- `metrics.csv`
- `bank_metrics.csv`
- `sample_decisions.csv`
- `transactions.csv`
- `test_transactions.csv`
- `predictions.csv`
- `artifacts/fds_model.pt`
- `artifacts/preprocessor.pkl`
- `artifacts/manifest.json`
- `final_report.md`

For the full-size local workflow:

```bash
python3 scripts/run_full_demo.py
```

Core experiment only:

```bash
python3 scripts/run_experiment.py --config configs/default.yaml
python3 scripts/predict_with_artifact.py
python3 scripts/generate_final_report.py
```

DP sweep can be run separately:

```bash
python3 scripts/run_dp_sweep.py --rounds 3 --samples-per-bank 1200
python3 scripts/run_opacus_dp.py --epochs 3 --noise-multiplier 1.0
```

Model poisoning scenarios can be run separately:

```bash
python3 scripts/run_poisoning_attack.py --rounds 3 --samples-per-bank 1200 --malicious-bank "Bank B"
```

Gradient leakage reconstruction can be run separately:

```bash
python3 scripts/run_gradient_leakage.py --iterations 120
```

Secure aggregation, streaming, and optional integrations:

```bash
python3 scripts/run_secure_aggregation.py --rounds 3 --samples-per-bank 1200
python3 scripts/run_streaming_simulation.py --mode file --samples-per-bank 100
python3 scripts/run_flower_simulation.py --rounds 3 --samples-per-bank 600
OPENAI_MODEL=<model> python3 scripts/run_llm_agent.py
```

Docker:

```bash
docker compose up experiment dashboard
docker compose --profile streaming up redpanda stream-simulator
```

## Project Layout

```text
src/sentinel_fds/
  agents/       AI security agent and response policy
  evaluation/   metrics helpers
  fl/           FedAvg orchestration
  models/       PyTorch FDS model and training
  privacy/      DP clipping/noise helpers
  simulation/   synthetic bank transaction generator
  streaming/    JSONL/Kafka transaction event publishing
dashboard/      Streamlit app
configs/        YAML experiment configs
scripts/        runnable experiment entrypoints
tests/          smoke tests
```

## Current Scope

The project is a local research/demo platform. It includes Flower simulation,
Opacus DP-SGD, secure aggregation simulation, attack experiments, dashboarding,
model artifact persistence, and Docker runtime files.

Operational checks still depend on the local environment:

- Docker daemon must be running for `docker compose`.
- Kafka mode needs a reachable broker, or the Redpanda compose profile.
- LLM report generation needs `OPENAI_API_KEY` and `OPENAI_MODEL`.
