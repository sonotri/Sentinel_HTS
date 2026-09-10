FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
COPY dashboard ./dashboard
COPY configs ./configs

RUN pip install --upgrade pip && pip install -r requirements.txt

ENV PYTHONPATH=/app/src

CMD ["python", "scripts/run_experiment.py", "--config", "configs/default.yaml"]
