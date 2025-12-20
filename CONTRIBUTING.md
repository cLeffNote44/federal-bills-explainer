# Contributing to Federal Bills Explainer

Thank you for your interest in contributing to the Federal Bills Explainer project! This document provides guidelines and instructions for contributing to this monorepo.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Development Setup

### Prerequisites

- **Python 3.11+** (3.13 also supported)
- **Node.js 18+** and pnpm
- **Docker Desktop** for PostgreSQL with pgvector
- **Git** for version control
- **Congress.gov API key** (get from https://api.congress.gov/sign-up/)

### Initial Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/federal-bills-explainer.git
cd federal-bills-explainer
```

2. **Set up environment files:**
```bash
# Infrastructure
cp infra/.env.example infra/.env

# Ingestion module
cp apps/ingestion/.env.example apps/ingestion/.env

# API
cp apps/api/.env.example apps/api/.env

# Frontend
cp apps/frontend/.env.local.example apps/frontend/.env.local
```

3. **Start Docker services:**
```bash
cd infra
docker compose up -d db
```

4. **Set up Python environment (Windows):**
```powershell
# Create virtual environment
py -3.11 -m venv .venv

# Activate
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

# Install core packages
pip install -e packages/py-core
pip install -e apps/ingestion
pip install -r apps/api/requirements.txt

# Install ML dependencies
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers
```

5. **Run database migrations:**
```powershell
$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/fbx"
py -m alembic -c apps\api\alembic.ini upgrade head
```

6. **Set up frontend:**
```bash
cd apps/frontend
pnpm install
```

## Project Structure

```
federal-bills-explainer/
├── apps/
│   ├── api/            # FastAPI backend
│   │   ├── alembic/    # Database migrations
│   │   ├── app/        # API application code
│   │   └── tests/      # API tests
│   ├── ingestion/      # Bill ingestion module
│   │   ├── fbx_ingest/ # Ingestion CLI and logic
│   │   └── tests/      # Ingestion tests
│   └── frontend/       # Next.js frontend
│       ├── src/        # Frontend source code
│       └── tests/      # Frontend tests
├── packages/
│   └── py-core/        # Shared Python core
│       └── fbx_core/   # Core models and utilities
├── infra/              # Infrastructure configuration
│   ├── docker-compose.yml
│   └── .env.example
└── .github/            # GitHub Actions workflows
```

## Development Workflow

### Branch Strategy

1. **Main branch:** `main` - Production-ready code
2. **Development branch:** `dev` - Integration branch
3. **Feature branches:** `feat/feature-name` - Individual features
4. **Bugfix branches:** `fix/bug-description` - Bug fixes
5. **Hotfix branches:** `hotfix/issue-description` - Production fixes

### Creating a Feature

1. **Create a feature branch:**
```bash
git checkout -b feat/your-feature-name
```

2. **Make your changes**

3. **Run tests:**
```bash
# Python tests
pytest apps/api/tests
pytest apps/ingestion/tests

# Frontend tests
cd apps/frontend
pnpm test
```

4. **Commit your changes:**
```bash
git add .
git commit -m "feat(module): description of feature"
```

### Commit Message Format

Follow the Conventional Commits specification:

```
type(scope): description

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples:**
```bash
feat(ingestion): add support for committee data
fix(api): correct pagination logic for bills endpoint
docs(readme): update setup instructions
```

## Code Style

### Python

- Follow PEP 8 style guide
- Use type hints where possible
- Format with Black: `black .`
- Lint with Flake8: `flake8 .`
- Sort imports with isort: `isort .`

### TypeScript/JavaScript

- Use ESLint configuration in the project
- Format with Prettier: `pnpm format`
- Run linter: `pnpm lint`

### SQL

- Use lowercase for keywords
- Indent with 2 spaces
- Name tables in plural form
- Use snake_case for column names

## Testing

### Running Tests

**Python (API & Ingestion):**
```bash
# All tests
pytest

# With coverage
pytest --cov=fbx_core --cov=fbx_ingest --cov-report=html

# Specific module
pytest apps/api/tests/
pytest apps/ingestion/tests/
```

**Frontend:**
```bash
cd apps/frontend
pnpm test
pnpm test:watch  # Watch mode
pnpm test:coverage  # With coverage
```

### Writing Tests

- Write unit tests for all new features
- Aim for >80% code coverage
- Use meaningful test names
- Mock external dependencies
- Test error cases

## Submitting Changes

### Pull Request Process

1. **Ensure all tests pass**
2. **Update documentation** if needed
3. **Create a pull request** with:
   - Clear title following commit format
   - Description of changes
   - Any breaking changes noted
   - Related issue numbers
4. **Request review** from maintainers
5. **Address review feedback**
6. **Merge** after approval

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No console errors
- [ ] Changes are backward compatible
```

## Common Tasks

### Adding a New Database Model

1. Create model in `packages/py-core/fbx_core/models/`
2. Import in `packages/py-core/fbx_core/models/__init__.py`
3. Create Alembic migration:
```bash
cd apps/api
alembic revision -m "add_new_model"
# Edit the generated migration file
alembic upgrade head
```

### Adding an API Endpoint

1. Create route in `apps/api/app/routers/`
2. Add service logic in `apps/api/app/services/`
3. Update OpenAPI documentation
4. Write tests in `apps/api/tests/`

### Updating Ingestion Logic

1. Modify `apps/ingestion/fbx_ingest/`
2. Test with dry-run:
```bash
python -m fbx_ingest.cli sync --dry-run --sample-bill 118-hr-1234
```
3. Update documentation in `apps/ingestion/README.md`

### Frontend Development

1. Create components in `apps/frontend/src/components/`
2. Add pages in `apps/frontend/src/app/`
3. Update types in `apps/frontend/src/types/`
4. Test locally: `pnpm dev`

## Troubleshooting

### Common Issues

**Docker Not Running:**
- Start Docker Desktop manually
- Wait for it to fully initialize
- Verify with: `docker ps`

**Database Connection Errors:**
```powershell
# Check if database is running
docker compose ps

# View logs
docker compose logs db --tail 50

# Restart if needed
docker compose restart db
```

**Module Import Errors:**
```powershell
# Reinstall in editable mode
pip install -e packages/py-core
pip install -e apps/ingestion
```

**Missing Dependencies:**
```powershell
# Python
pip install -r requirements.txt

# Frontend
cd apps/frontend
pnpm install
```

**PowerShell Execution Policy (Windows):**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Environment Variables

Required environment variables:

**Ingestion (.env):**
- `INGEST_CONGRESS_API_KEY`: Congress.gov API key
- `INGEST_DATABASE_URL`: PostgreSQL connection string
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

**API (.env):**
- `DATABASE_URL`: PostgreSQL connection string
- `FRONTEND_URL`: Frontend URL for CORS
- `SECRET_KEY`: JWT secret key

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_URL`: Backend API URL

## Getting Help

- Check existing issues on GitHub
- Review documentation in README files
- Ask questions in discussions
- Contact maintainers

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Follow project guidelines

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- CHANGELOG.md for significant contributions
- Project documentation

Thank you for contributing to Federal Bills Explainer!