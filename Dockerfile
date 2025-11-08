# Base
FROM python:3.10-slim AS base_shared

WORKDIR /code
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev
ENV PATH="/code/.venv/bin/:$PATH"

# App
FROM base_shared AS app
WORKDIR /code
COPY . .
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Worker_GPU
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04 AS worker

RUN apt-get update && apt-get install -y python3 python3-venv python3-pip git-lfs && \
    python3 -m pip install --upgrade pip && rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev
COPY . .
WORKDIR /code
CMD ["uv", "run", "-m", "worker.worker"]