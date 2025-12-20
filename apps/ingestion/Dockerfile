# Build with repo root as context:
#   docker build -f apps/ingestion/Dockerfile .
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install core first (cache-friendly)
COPY packages/py-core /app/packages/py-core
RUN pip install --no-cache-dir -e /app/packages/py-core

# Install ingestion deps
COPY apps/ingestion/requirements.txt /app/apps/ingestion/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/ingestion/requirements.txt

# Copy ingestion code
COPY apps/ingestion /app/apps/ingestion

WORKDIR /app/apps/ingestion

# Default command shows help
CMD ["python", "-m", "fbx_ingest.cli", "--help"]
