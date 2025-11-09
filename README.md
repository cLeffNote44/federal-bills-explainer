# Federal Bills Explainer

A monorepo for a federal legislation explainer that helps citizens understand federal laws through AI-generated explanations.

## Overview

- **Backend**: FastAPI (Python) exposing endpoints for bills, explanations, and semantic search
- **Ingestion**: CLI tool that fetches US federal bills, generates plain-language explanations using local ML models, and creates semantic embeddings
- **Data store**: PostgreSQL with pgvector extension (Neon in prod, Docker in dev)
- **Frontend**: Next.js application on Vercel for user interface

## Tech Stack

### Data Pipeline
- **Federal data source**: Congress.gov API (most detailed, free with API key)
- **Explanation generation**: Local OSS models (Google Flan-T5 or Microsoft Phi-3)
- **Semantic embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Vector storage**: PostgreSQL with pgvector extension

### Infrastructure
- **Backend API**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL 15+ with pgvector
- **Frontend**: Next.js 14 with TypeScript
- **Containerization**: Docker Compose for local development
- **CI/CD**: GitHub Actions for automated workflows

## Quick Start

### Prerequisites
- Python 3.11+ (3.13 also supported)
- Node.js 18+ and pnpm
- Docker Desktop
- Congress.gov API key (get from https://api.congress.gov/sign-up/)

### Windows PowerShell Setup

1) **Start Database and API via Docker:**
```powershell
cp infra/.env.example infra/.env
# Edit infra/.env with your settings
cd infra
docker compose up -d db
```

2) **Set up and run ingestion module:**
```powershell
cd apps\ingestion
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -e ..\..\packages\py-core
pip install -e .
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers

# Test with a sample bill
python -m fbx_ingest.cli sync --dry-run --sample-bill 117-hr-3076
```

3) Start frontend
```powershell
cd apps/frontend
cp .env.local.example .env.local
pnpm install
pnpm dev
```

4) Browse
- API: http://localhost:8000/healthz and /bills
- Frontend: http://localhost:3000

## Repository Structure

```
apps/
  api/         # FastAPI backend + Alembic migrations
  ingestion/   # CLI tool for bill ingestion and ML processing
  frontend/    # Next.js frontend application
packages/
  py-core/     # Shared Python core (models, utilities, services)
infra/         # Docker Compose and environment configs
.github/       # GitHub Actions CI/CD workflows
```

## Key Features

- **Automated Ingestion**: Fetches federal bills that became law from Congress.gov
- **AI Explanations**: Generates plain-language explanations using local ML models
- **Semantic Search**: Vector embeddings enable intelligent search capabilities
- **RESTful API**: FastAPI backend with automatic OpenAPI documentation
- **Modern UI**: Responsive Next.js frontend with TypeScript
- **Scalable Architecture**: Modular monorepo structure with shared packages

## Documentation

- [Ingestion Module README](apps/ingestion/README.md) - Detailed setup and usage for the ingestion CLI
- [API Documentation](apps/api/README.md) - Backend API setup and endpoints
- [Frontend Documentation](apps/frontend/README.md) - Frontend development guide
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute to the project

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:
- Development setup
- Code style and standards
- Testing requirements
- Pull request process

## License

This project is licensed under the MIT License - see the LICENSE file for details.
