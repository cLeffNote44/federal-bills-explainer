# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive project audit and production readiness improvements
- SECURITY.md with vulnerability reporting guidelines
- CODE_OF_CONDUCT.md based on Contributor Covenant 2.1
- CHANGELOG.md for tracking version history
- CONTRIBUTORS.md for acknowledging contributors
- .dockerignore files for optimized Docker builds
- .editorconfig for consistent coding style
- Makefile for common development commands
- Pre-commit hooks configuration
- Dependabot configuration for automated dependency updates
- .nvmrc for Node.js version pinning
- Frontend production Dockerfile
- Environment variable validation
- Security headers middleware
- Rate limiting for all API endpoints
- JWT authentication implementation
- Input validation and sanitization
- Comprehensive test suite (unit, integration, E2E)
- Playwright E2E tests for frontend
- Redis caching layer implementation
- API versioning (/api/v1/)
- Celery queue system for background jobs
- Data export functionality (CSV, JSON)
- Bill categories and tagging system
- Monitoring with Prometheus and Grafana
- Kubernetes Helm charts
- Monitoring dashboards and alerting rules
- Health check endpoints with detailed status
- Request/response logging middleware
- Database connection pooling
- Graceful shutdown handling
- Performance benchmarks
- Load testing configuration
- API documentation improvements
- Architecture decision records (ADRs)
- Deployment runbooks
- Backup and disaster recovery procedures

### Changed
- Updated all Python dependencies to latest stable versions
- Updated all frontend dependencies to latest versions
- Upgraded Next.js to v15
- Upgraded ESLint to v9
- Upgraded Vitest to v2
- Pinned all Docker image versions
- Improved CI/CD pipeline with strict testing
- Enhanced security configuration in docker-compose.yml
- Removed weak default passwords and secrets
- Improved CORS configuration
- Updated documentation with comprehensive guides
- Reorganized test structure for better maintainability
- Enhanced error handling across all modules
- Improved logging with structured format
- Optimized Docker layer caching

### Fixed
- README typo: "leasat" → "least"
- CI tests now properly fail on errors (removed || true)
- Security vulnerabilities in dependencies
- Docker image bloat with proper .dockerignore
- Inconsistent environment variable naming
- Missing type hints in Python code
- CORS issues for production deployment
- Database connection leaks
- Race conditions in concurrent operations
- Memory leaks in long-running processes

### Security
- Implemented proper secrets management
- Added security headers (CSP, HSTS, X-Frame-Options, etc.)
- Enabled rate limiting on all API endpoints
- Added input validation and sanitization
- Implemented JWT authentication
- Configured HTTPS enforcement
- Added request size limits
- Removed exposed database ports from public access
- Strengthened pgAdmin security
- Added security scanning in CI that fails on vulnerabilities
- Implemented audit logging
- Added dependency vulnerability scanning
- Configured Content Security Policy
- Enabled CORS with strict origins

### Deprecated
- Simple admin token authentication (replaced with JWT)

### Removed
- Weak default passwords from docker-compose.yml
- Hardcoded secrets from configuration files
- || true error suppression from CI workflows
- Unused dependencies from requirements files

## [1.0.0] - 2025-11-09

### Added
- Initial release of Federal Bills Explainer
- FastAPI backend with RESTful endpoints
- Next.js 14 frontend with TypeScript
- PostgreSQL database with pgvector extension
- Bill ingestion pipeline from Congress.gov
- AI-powered explanation generation (Flan-T5, Phi-3)
- Semantic search with sentence-transformers
- Docker Compose setup for local development
- GitHub Actions CI/CD pipeline
- Database migrations with Alembic
- Rate limiting for Congress.gov API
- Job tracking and monitoring
- Incremental/delta ingestion
- Batch processing with parallelization
- Database performance optimization
- Kubernetes manifests for deployment
- Comprehensive documentation (README, CONTRIBUTING, WARP.md)
- MIT License

### Key Features
- Automated bill fetching from Congress.gov
- Plain-language explanations using local LLM models
- Vector similarity search for bills
- Interactive API documentation
- Responsive web interface
- Modular monorepo architecture
- Production-ready infrastructure

---

## Release Types

- **Major version** (X.0.0): Breaking changes, major new features
- **Minor version** (1.X.0): New features, backwards compatible
- **Patch version** (1.0.X): Bug fixes, security patches

## Categories

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

---

[Unreleased]: https://github.com/cLeffNote44/federal-bills-explainer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/cLeffNote44/federal-bills-explainer/releases/tag/v1.0.0
