.PHONY: help install dev test lint format clean docker-up docker-down migrate db-shell api-shell frontend-dev ingest-dry ingest-live backup restore security-scan docs

# Default target
.DEFAULT_GOAL := help

# Color output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)Federal Bills Explainer - Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Installation

install: ## Install all dependencies
	@echo "$(GREEN)Installing Python dependencies...$(NC)"
	pip install -e packages/py-core
	pip install -r requirements.txt
	@echo "$(GREEN)Installing frontend dependencies...$(NC)"
	cd apps/frontend && pnpm install
	@echo "$(GREEN)Setting up pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)Installation complete!$(NC)"

install-dev: ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	pip install -e packages/py-core[dev]
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio black ruff mypy pre-commit bandit safety
	cd apps/frontend && pnpm install --dev
	pre-commit install
	@echo "$(GREEN)Development environment ready!$(NC)"

setup-env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(RED)IMPORTANT: Update .env with your actual values!$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

##@ Development

dev: docker-up ## Start full development environment
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "$(BLUE)API: http://localhost:8000$(NC)"
	@echo "$(BLUE)Frontend: http://localhost:3000$(NC)"
	@echo "$(BLUE)API Docs: http://localhost:8000/docs$(NC)"

api-dev: ## Start API development server
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev: ## Start frontend development server
	cd apps/frontend && pnpm dev

api-shell: ## Open Python shell with API context
	cd apps/api && python -m IPython

db-shell: ## Open PostgreSQL shell
	docker compose exec db psql -U fbx_user -d federal_bills

##@ Docker

docker-up: ## Start all Docker services
	@echo "$(GREEN)Starting Docker services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)Services started. Waiting for database...$(NC)"
	@sleep 5
	@echo "$(GREEN)Running migrations...$(NC)"
	@make migrate
	@echo "$(GREEN)Docker environment ready!$(NC)"

docker-down: ## Stop all Docker services
	@echo "$(YELLOW)Stopping Docker services...$(NC)"
	docker compose down

docker-restart: ## Restart all Docker services
	@make docker-down
	@make docker-up

docker-logs: ## View logs from all services
	docker compose logs -f

docker-clean: ## Remove all Docker containers, volumes, and images
	@echo "$(RED)Cleaning Docker environment...$(NC)"
	docker compose down -v
	docker system prune -f
	@echo "$(GREEN)Docker environment cleaned$(NC)"

##@ Database

migrate: ## Run database migrations
	@echo "$(GREEN)Running migrations...$(NC)"
	cd apps/api && alembic upgrade head

migrate-create: ## Create a new migration (use NAME=migration_name)
	@if [ -z "$(NAME)" ]; then \
		echo "$(RED)Error: Please provide NAME=migration_name$(NC)"; \
		exit 1; \
	fi
	cd apps/api && alembic revision --autogenerate -m "$(NAME)"

migrate-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	cd apps/api && alembic downgrade -1

migrate-history: ## Show migration history
	cd apps/api && alembic history

db-reset: ## Reset database (WARNING: deletes all data)
	@echo "$(RED)This will delete ALL data. Press Ctrl+C to cancel, or wait 5 seconds...$(NC)"
	@sleep 5
	docker compose down -v
	docker compose up -d db
	@sleep 5
	@make migrate
	@echo "$(GREEN)Database reset complete$(NC)"

##@ Ingestion

ingest-dry: ## Run ingestion in dry-run mode (no DB writes)
	@echo "$(YELLOW)Running ingestion in dry-run mode...$(NC)"
	python -m fbx_ingest.cli sync --dry-run

ingest-live: ## Run live ingestion (writes to DB)
	@echo "$(GREEN)Running live ingestion...$(NC)"
	python -m fbx_ingest.cli sync --no-dry-run

ingest-sample: ## Ingest a sample bill (BILL=118-hr-1234)
	@if [ -z "$(BILL)" ]; then \
		echo "$(YELLOW)Using default sample bill: 117-hr-3076$(NC)"; \
		python -m fbx_ingest.cli sync --dry-run --sample-bill 117-hr-3076; \
	else \
		python -m fbx_ingest.cli sync --dry-run --sample-bill $(BILL); \
	fi

ingest-jobs: ## Show ingestion job status
	python -m fbx_ingest.cli jobs --stats

ingest-rate-limits: ## Check rate limit status
	python -m fbx_ingest.cli rate-limits

##@ Testing

test: ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	pytest

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	pytest -m unit

test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	pytest -m integration

test-e2e: ## Run E2E tests
	@echo "$(GREEN)Running E2E tests...$(NC)"
	cd apps/frontend && pnpm test:e2e

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	pytest --cov=apps --cov=packages --cov-report=html --cov-report=term-missing
	@echo "$(BLUE)Coverage report: htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	pytest-watch

##@ Code Quality

lint: ## Run all linters
	@echo "$(GREEN)Running Python linters...$(NC)"
	black --check packages/py-core apps/api apps/ingestion
	ruff check .
	mypy packages/py-core --ignore-missing-imports
	@echo "$(GREEN)Running frontend linters...$(NC)"
	cd apps/frontend && pnpm lint

format: ## Format all code
	@echo "$(GREEN)Formatting Python code...$(NC)"
	black packages/py-core apps/api apps/ingestion
	ruff check --fix .
	@echo "$(GREEN)Formatting frontend code...$(NC)"
	cd apps/frontend && pnpm format || true

type-check: ## Run type checking
	@echo "$(GREEN)Type checking Python...$(NC)"
	mypy packages/py-core apps/api apps/ingestion --ignore-missing-imports
	@echo "$(GREEN)Type checking TypeScript...$(NC)"
	cd apps/frontend && pnpm tsc --noEmit

security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	bandit -r packages apps -f json -o bandit-report.json || true
	safety check || true
	@echo "$(BLUE)Security report: bandit-report.json$(NC)"

##@ Cleanup

clean: ## Clean generated files
	@echo "$(YELLOW)Cleaning generated files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf build/
	cd apps/frontend && rm -rf .next/ out/ node_modules/.cache/ 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-all: clean docker-clean ## Clean everything including Docker

##@ Production

build: ## Build production Docker images
	@echo "$(GREEN)Building production images...$(NC)"
	docker compose -f docker-compose.yml build

deploy-k8s: ## Deploy to Kubernetes
	@echo "$(GREEN)Deploying to Kubernetes...$(NC)"
	kubectl apply -k infra/k8s/overlays/prod

health-check: ## Check service health
	@echo "$(GREEN)Checking service health...$(NC)"
	@curl -s http://localhost:8000/monitoring/health | python -m json.tool

##@ Monitoring

logs-api: ## View API logs
	docker compose logs -f api

logs-frontend: ## View frontend logs
	docker compose logs -f frontend

logs-ingestion: ## View ingestion logs
	docker compose logs -f ingestion

logs-db: ## View database logs
	docker compose logs -f db

stats: ## Show service statistics
	docker compose stats

##@ Backup & Restore

backup: ## Backup database
	@echo "$(GREEN)Creating database backup...$(NC)"
	@mkdir -p backups
	docker compose exec -T db pg_dump -U fbx_user federal_bills > backups/backup-$$(date +%Y%m%d-%H%M%S).sql
	@echo "$(GREEN)Backup created in backups/$(NC)"

restore: ## Restore database (use FILE=backups/backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please provide FILE=backups/backup.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Restoring database from $(FILE)...$(NC)"
	docker compose exec -T db psql -U fbx_user federal_bills < $(FILE)
	@echo "$(GREEN)Database restored$(NC)"

##@ Documentation

docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	@echo "$(BLUE)API docs available at: http://localhost:8000/docs$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	@python -m http.server 8080 --directory docs

##@ Utilities

version: ## Show version information
	@echo "$(BLUE)Python version:$(NC)"
	@python --version
	@echo "$(BLUE)Node version:$(NC)"
	@node --version
	@echo "$(BLUE)pnpm version:$(NC)"
	@pnpm --version
	@echo "$(BLUE)Docker version:$(NC)"
	@docker --version

status: ## Show current status
	@echo "$(BLUE)=== Docker Services ===$(NC)"
	@docker compose ps
	@echo ""
	@echo "$(BLUE)=== Database ===$(NC)"
	@docker compose exec db psql -U fbx_user -d federal_bills -c "SELECT COUNT(*) as bill_count FROM bills;" 2>/dev/null || echo "Database not available"

pre-commit-all: ## Run pre-commit on all files
	pre-commit run --all-files

update-deps: ## Update all dependencies
	@echo "$(GREEN)Updating Python dependencies...$(NC)"
	pip list --outdated
	@echo "$(GREEN)Updating frontend dependencies...$(NC)"
	cd apps/frontend && pnpm update --latest
