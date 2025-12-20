# Build with repo root as context:
#   docker build -f apps/api/Dockerfile .
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install core first (cache-friendly)
COPY packages/py-core /app/packages/py-core
RUN pip install --no-cache-dir -e /app/packages/py-core

# Install API deps
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

# Copy app and alembic
COPY apps/api/app /app/apps/api/app
COPY apps/api/alembic /app/apps/api/alembic
COPY apps/api/alembic.ini /app/apps/api/alembic.ini

# Include fixtures for dry-run or no-API-key scenarios
COPY apps/ingestion/fixtures /app/apps/ingestion/fixtures

WORKDIR /app/apps/api
ENV PORT=8000
EXPOSE 8000

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000

