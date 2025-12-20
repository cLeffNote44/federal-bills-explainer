# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

This is a monorepo for a Federal Bills Explainer that helps citizens understand federal laws through AI-generated explanations:
- **Backend**: FastAPI (Python 3.11+) with SQLAlchemy, Alembic, PostgreSQL + pgvector
- **Frontend**: Next.js 14 with TypeScript, React 18, Tailwind CSS
- **Ingestion**: CLI tool that fetches bills from Congress.gov and generates AI explanations/embeddings
- **Database**: PostgreSQL with pgvector extension for semantic search
- **Shared Core**: Python package with domain models and utilities
- **Infrastructure**: Docker Compose for local development

## High-level Architecture

### Data Flow
1. **Ingestion Pipeline**:
   - Fetches federal bills from Congress.gov API (requires API key)
   - Generates plain-language explanations using local ML models (Flan-T5/Phi-3)
   - Creates vector embeddings using sentence-transformers
   - Stores in PostgreSQL with pgvector for semantic search

2. **Serving Layer**:
   - FastAPI backend exposes REST APIs for bills, explanations, and search
   - Next.js frontend consumes the API
   - Redis caching layer (optional)

### Repository Structure
```
apps/
  api/         # FastAPI backend + Alembic migrations
  ingestion/   # CLI tool for bill ingestion and ML processing
  frontend/    # Next.js frontend application
packages/
  py-core/     # Shared Python core (models, utilities)
infra/         # Docker Compose and environment configs
```

## Prerequisites

- **Python 3.11+** (3.13 also supported)
- **Node.js 18+** and pnpm (lockfile present: pnpm-lock.yaml)
- **Docker Desktop** with Compose v2
- **Congress.gov API key** (get from https://api.congress.gov/sign-up/)
- **Git**

## Quick Start (Docker Compose)

```powershell
# Copy environment files
Copy-Item infra/.env.example infra/.env
Copy-Item apps/ingestion/.env.example apps/ingestion/.env
Copy-Item apps/frontend/.env.local.example apps/frontend/.env.local

# Edit .env files with your API keys and settings

# Start services
cd infra
docker compose up -d

# Check status
docker compose ps

# Access services
# API: http://localhost:8000/healthz
# Frontend: http://localhost:3000
```

## Local Development

### Database Setup

```powershell
# Start PostgreSQL with pgvector
cd infra
docker compose up -d db

# Verify it's running
docker compose logs db --tail 20

# Run migrations
$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/fbx"
cd ../apps/api
alembic upgrade head
```

### Backend (FastAPI)

```powershell
# Navigate to API directory
cd apps/api

# Install dependencies
pip install -r requirements.txt
pip install -e ../../packages/py-core

# Set environment variables
$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/fbx"
$env:CORS_ORIGINS = "http://localhost:3000"

# Run development server
uvicorn app.main:app --reload --port 8000

# API docs available at http://localhost:8000/docs
```

### Frontend (Next.js)

```powershell
# Navigate to frontend
cd apps/frontend

# Install dependencies (using pnpm)
pnpm install

# Set environment variables
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"

# Run development server
pnpm dev

# Access at http://localhost:3001
```

### Ingestion Module

```powershell
# Navigate to ingestion
cd apps/ingestion

# Create and activate virtual environment
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ../../packages/py-core
pip install -e .
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers

# Set environment variables
$env:INGEST_CONGRESS_API_KEY = "your_congress_api_key"
$env:INGEST_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/fbx"

# Test configuration
python -m fbx_ingest.cli test

# Run ingestion
python -m fbx_ingest.cli sync --dry-run --sample-bill 117-hr-3076
python -m fbx_ingest.cli sync --no-dry-run --from-date 2024-01-01 --to-date 2024-12-31 --max-records 10
```

## Testing

### Python Tests (pytest)

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov=packages --cov-report=term-missing

# Run specific test file
pytest apps/api/tests/test_bills.py

# Run tests matching pattern
pytest -k "test_bill"

# Run with markers
pytest -m "not slow"
pytest -m "unit"
```

### Frontend Tests (vitest)

```powershell
cd apps/frontend

# Run all tests
pnpm test

# Watch mode
pnpm vitest

# With coverage
pnpm test --coverage
```

## Linting and Formatting

### Python

```powershell
# Format with Black
black packages/py-core apps/api apps/ingestion

# Lint with Ruff
ruff check .

# Type checking with mypy
mypy packages/py-core --ignore-missing-imports
```

### TypeScript/JavaScript

```powershell
cd apps/frontend

# Lint
pnpm lint

# Format (if configured)
pnpm format
```

## Database and Migrations

### Alembic Commands

```powershell
cd apps/api

# Create new migration
alembic revision -m "Add new feature"

# Auto-generate migration
alembic revision --autogenerate -m "Add bills table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current revision
alembic current

# View history
alembic history
```

### pgvector Setup

```powershell
# If not auto-created, enable pgvector extension
docker compose exec db psql -U postgres -d fbx -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Common Commands

### Docker Operations

```powershell
# Start all services
docker compose up -d

# View logs
docker compose logs -f
docker compose logs api --tail 100

# Rebuild images
docker compose build

# Stop services
docker compose down

# Reset everything (destructive)
docker compose down -v
```

### Development Workflow

```powershell
# Start database
cd infra
docker compose up -d db

# Run migrations
cd ../apps/api
$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/fbx"
alembic upgrade head

# Start API server
uvicorn app.main:app --reload

# In another terminal, start frontend
cd apps/frontend
pnpm dev

# Run ingestion (dry run first)
cd apps/ingestion
python -m fbx_ingest.cli sync --dry-run --sample-bill 117-hr-3076
```

### Data Ingestion Examples

```powershell
# Test with specific bill
python -m fbx_ingest.cli sync --dry-run --sample-bill 118-hr-2882

# Ingest recent bills
python -m fbx_ingest.cli sync --no-dry-run --from-date 2024-06-01 --to-date 2024-06-30 --max-records 10

# Daily ingestion
$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$today = (Get-Date).ToString("yyyy-MM-dd")
python -m fbx_ingest.cli sync --no-dry-run --from-date $yesterday --to-date $today
```

## Configuration

### Required Environment Variables

**Backend/API (.env)**:
- `DATABASE_URL` - PostgreSQL connection string
- `CORS_ORIGINS` - Allowed CORS origins
- `ADMIN_TOKEN` - Admin authentication token
- `EMBEDDING_MODEL` - Model for embeddings (default: sentence-transformers/all-MiniLM-L6-v2)
- `EXPLAIN_MODEL` - Model for explanations (default: google/flan-t5-base)

**Ingestion (.env)**:
- `INGEST_CONGRESS_API_KEY` - Congress.gov API key (required)
- `INGEST_DATABASE_URL` - PostgreSQL connection string
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)
- `INGEST_USE_GPU` - Enable GPU acceleration (true/false)

**Frontend (.env.local)**:
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)

### Default Ports
- Backend API: 8000
- Frontend: 3001 (configured in package.json)
- PostgreSQL: 5432
- Redis: 6379

## Windows PowerShell Tips

```powershell
# Set environment variable (session only)
$env:VARIABLE_NAME = "value"

# Copy files
Copy-Item source.txt destination.txt

# Check port usage
Get-NetTCPConnection -LocalPort 8000

# Kill process using port
Get-NetTCPConnection -LocalPort 8000 | Select-Object -First 1 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Enable pnpm via Corepack
corepack enable
corepack prepare pnpm@latest --activate
```

## Troubleshooting

### Common Issues

**ModuleNotFoundError for fbx_core**:
```powershell
# Reinstall in editable mode
pip install -e packages/py-core
pip install -e apps/ingestion
```

**Database Connection Issues**:
```powershell
# Check if PostgreSQL is running
docker compose ps

# Check logs
docker compose logs db --tail 50

# Verify connection string
echo $env:DATABASE_URL
```

**Port Already in Use**:
```powershell
# Windows: Find and kill process
Get-NetTCPConnection -LocalPort 8000 | Select-Object -First 1 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

**PowerShell Execution Policy**:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# Or permanently for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Missing ML Models**:
Models are cached in `%USERPROFILE%\.cache\huggingface`. First run downloads them automatically.

**Frontend Can't Reach Backend**:
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify backend is running on expected port
- Check browser console for CORS errors

## CI/CD

GitHub Actions workflows run on push/PR:
- **Linting**: Black, Ruff, mypy for Python
- **Testing**: pytest for backend/ingestion, vitest for frontend
- **Security**: Bandit and Safety scans
- **Docker**: Build validation
- **Database**: Tests run against PostgreSQL with pgvector

## Additional Resources

- [README.md](README.md) - Project overview and setup
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [Ingestion README](apps/ingestion/README.md) - Detailed ingestion documentation
- [Congress.gov API](https://api.congress.gov/) - Data source documentation