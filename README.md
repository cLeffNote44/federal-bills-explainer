# Federal Bills Explainer

[![CI](https://github.com/cLeffNote44/federal-bills-explainer/actions/workflows/ci.yml/badge.svg)](https://github.com/cLeffNote44/federal-bills-explainer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Did you also take a look at the "Big Beautiful Bill (bloat)" and think, what in the name of??....****
**Yeah well I did too. So I built this to help the fool in all of us understand what it is they do in washington**
**...or at least try**

📧 Email me with feedback: **cLeffNote44@pm.me**


> An AI-powered platform that makes federal legislation accessible to everyone through plain-language explanations and semantic search.

## Overview

**Federal Bills Explainer** is a comprehensive solution for understanding US federal legislation. It combines modern web technologies with AI/ML to transform complex legal text into clear, understandable explanations.

### Key Components

- **FastAPI Backend**: RESTful API with automatic documentation, semantic search, and bill management
- **Ingestion Pipeline**: Automated CLI tool for fetching bills from Congress.gov and generating AI explanations
- **Next.js Frontend**: Modern, responsive web interface for browsing and searching bills
- **PostgreSQL + pgvector**: Scalable database with vector similarity search capabilities

## Tech Stack

### Data Pipeline
- **Federal data source**: Congress.gov API (most detailed, free with API key)
- **Explanation generation**: Local OSS models (Google Flan-T5 or Microsoft Phi-3)
- **Semantic embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Vector storage**: PostgreSQL with pgvector extension

### Infrastructure
- **Backend API**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL 15+ with pgvector
- **Frontend**: Next.js 15 with TypeScript
- **Containerization**: Docker Compose for local development
- **CI/CD**: GitHub Actions for automated workflows

## Quick Start

### Prerequisites
- Python 3.11+ (3.13 also supported)
- Node.js 18+ and pnpm
- Docker Desktop
- Congress.gov API key (get from https://api.congress.gov/sign-up/)

### Development Setup

1) **Start Infrastructure:**
```powershell
# Copy and configure environment file
cp .env.example .env
# Edit .env with your settings (database credentials, API keys, etc.)

# Start all services with Docker Compose
docker compose up -d
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

4) **Access the Application:**
- API Documentation: http://localhost:8000/docs
- API Health Check: http://localhost:8000/healthz
- Frontend: http://localhost:3001

## Repository Structure

```
apps/
  api/         # FastAPI backend with RESTful endpoints
  ingestion/   # Bill ingestion pipeline with AI processing
  frontend/    # Next.js web application
packages/
  py-core/     # Shared Python package (models, database, utilities)
infra/         # Kubernetes deployment configurations
.github/       # CI/CD workflows and automation
```

## Key Features

- **Automated Ingestion**: Fetches federal bills that became law from Congress.gov
- **AI Explanations**: Generates plain-language explanations using local ML models
- **Semantic Search**: Vector embeddings enable intelligent search capabilities
- **RESTful API**: FastAPI backend with automatic OpenAPI documentation
- **Modern UI**: Responsive Next.js frontend with TypeScript
- **Scalable Architecture**: Modular monorepo structure with shared packages

## Documentation

- **[Ingestion Module](apps/ingestion/README.md)** - Detailed setup and usage for the bill ingestion pipeline
- **[Contributing Guidelines](CONTRIBUTING.md)** - Development setup, code standards, and contribution process
- **[Implementation Status](IMPLEMENTATION_STATUS.md)** - Current features and roadmap
- **[API Documentation](http://localhost:8000/docs)** - Interactive API documentation (when running)

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:
- Development setup
- Code style and standards
- Testing requirements
- Pull request process

## License

This project is licensed under the MIT License - see the LICENSE file for details.
