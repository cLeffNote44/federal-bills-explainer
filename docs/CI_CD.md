# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Federal Bills Explainer project.

## Overview

The project uses GitHub Actions for automated testing, building, and deployment. The pipeline consists of three main workflows:

1. **PR Checks** - Runs on every pull request
2. **Staging Deployment** - Auto-deploys to staging on `develop` branch
3. **Production Deployment** - Deploys to production on `main` branch or version tags

## Workflows

### 1. PR Checks (`ci-pr.yml`)

**Trigger:** Pull requests to `main` or `develop`

**Jobs:**

#### Code Quality (10 min)
- ESLint for TypeScript/JavaScript
- TypeScript type checking
- Python linting (flake8)
- Python formatting (black)
- Python import sorting (isort)

#### Frontend Tests (15 min)
- Unit tests with Jest
- Coverage reporting to Codecov

#### API Tests (15 min)
- PyTest with PostgreSQL and Redis
- Coverage reporting to Codecov

#### E2E Tests (20 min)
- Playwright tests across browsers
- Accessibility testing with axe-core
- Artifact upload for test reports

#### Build Verification (15 min)
- Next.js production build
- Bundle size analysis

#### Security Scan (10 min)
- Trivy vulnerability scanning
- npm audit
- pip-audit

#### PR Summary
- Posts results to PR as a comment
- Shows status of all jobs

**Total Runtime:** ~20 minutes (jobs run in parallel)

### 2. Staging Deployment (`deploy-staging.yml`)

**Trigger:** Push to `develop` branch or manual dispatch

**Environment:** staging

**Steps:**

1. **Build** (5 min)
   - Build frontend with staging environment variables
   - Install dependencies

2. **Database Migrations** (2 min)
   - Run Alembic migrations on staging database

3. **Docker Build & Push** (10 min)
   - Build API and Frontend Docker images
   - Tag with `staging-{sha}` and `staging-latest`
   - Push to Docker registry

4. **Deploy** (3 min)
   - SSH to staging server
   - Pull latest images
   - Restart containers with docker-compose
   - Wait for health checks

5. **Smoke Tests** (2 min)
   - Test API health endpoint
   - Test frontend accessibility

6. **Notifications**
   - Success/failure notifications to Slack
   - Rollback on failure

**Total Runtime:** ~15-20 minutes

### 3. Production Deployment (`deploy-production.yml`)

**Trigger:**
- Push to `main` branch
- Version tags (`v*`)
- Manual dispatch with version input

**Environment:** production (requires approval)

**Jobs:**

#### Pre-deployment Checks (10 min)
- Validate version tag format
- Check for breaking changes in CHANGELOG

#### Build and Test (20 min)
- Full test suite (all previous tests)
- Build production artifacts
- Upload artifacts for deployment

#### Production Deployment (30 min)
1. **Backup** (5 min)
   - Create database backup
   - Backup current deployment configuration

2. **Database Migrations** (5 min)
   - Run migrations on production database

3. **Docker Build & Push** (10 min)
   - Build with production optimizations
   - Tag with version, sha, and `latest`

4. **Zero-Downtime Deploy** (5 min)
   - Rolling update strategy
   - Scale up new containers before removing old
   - Health check verification

5. **Health Checks** (3 min)
   - API health verification
   - Frontend accessibility check
   - Smoke tests on critical paths

6. **Notifications & Release** (2 min)
   - Slack notification
   - Create GitHub Release with notes

#### Rollback (Manual)
- Triggered automatically on failure
- Restores database backup
- Reverts to previous container version

**Total Runtime:** ~30-40 minutes

### 4. Database Migrations (`database-migrations.yml`)

**Trigger:**
- PR with database changes
- Manual workflow dispatch

**On PR:**
- Validate migration scripts
- Check for conflicts (multiple heads)
- Test upgrade and downgrade
- Warn about destructive operations
- Generate migration summary

**On Manual Dispatch:**
- Create database backup
- Run migrations (upgrade or downgrade)
- Verify migration success
- Notify via Slack

## Environment Secrets

### Required Secrets

Configure these in GitHub Settings > Secrets:

#### Staging
```
STAGING_HOST               - Staging server hostname
STAGING_USER               - SSH username
STAGING_SSH_KEY            - SSH private key
STAGING_DATABASE_URL       - PostgreSQL connection string
STAGING_API_URL            - API base URL
```

#### Production
```
PRODUCTION_HOST            - Production server hostname
PRODUCTION_USER            - SSH username
PRODUCTION_SSH_KEY         - SSH private key
PRODUCTION_DATABASE_URL    - PostgreSQL connection string
```

#### Docker Registry
```
DOCKER_REGISTRY            - Registry URL (docker.io)
DOCKER_USERNAME            - Registry username
DOCKER_PASSWORD            - Registry password/token
```

#### Notifications (Optional)
```
SLACK_WEBHOOK_URL          - Slack webhook for notifications
```

#### Code Coverage
```
CODECOV_TOKEN              - Codecov upload token
```

## Branch Strategy

```
main (production)
  └─ develop (staging)
      └─ feature/* (PR checks only)
```

**Development Flow:**
1. Create feature branch from `develop`
2. Open PR → triggers CI checks
3. After approval, merge to `develop` → auto-deploys to staging
4. Test on staging
5. Merge `develop` to `main` → deploys to production

## Pre-commit Hooks

Local checks before commit (faster feedback):

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**Hooks include:**
- Code formatting (Black, Prettier)
- Linting (flake8, ESLint)
- Type checking (mypy)
- Security checks (bandit, detect-secrets)
- Commit message validation

## Manual Workflows

### Deploying a Specific Version

1. Go to Actions tab in GitHub
2. Select "Deploy to Production"
3. Click "Run workflow"
4. Enter version (e.g., `v1.2.3`)
5. Confirm deployment

### Running Database Migrations

1. Go to Actions tab
2. Select "Database Migrations"
3. Click "Run workflow"
4. Choose:
   - Environment (staging/production)
   - Direction (upgrade/downgrade)
   - Target revision (optional)
5. Confirm

### Emergency Rollback

**Option 1: Via GitHub Actions**
1. Find failed deployment run
2. Check "rollback" job
3. Manually trigger if needed

**Option 2: SSH to Server**
```bash
ssh user@server
cd /opt/federal-bills-explainer
./scripts/rollback.sh
```

## Monitoring Deployments

### GitHub Actions Dashboard
- View all workflow runs
- Check logs for failures
- Download artifacts (test reports, build outputs)

### Slack Notifications
All deployments send notifications with:
- ✅ Success status
- ❌ Failure alerts with logs link
- 🚀 Deployment details (version, commit, author)

### Health Check URLs

**Staging:**
- API: https://staging-api.federalbills.example.com/monitoring/health
- Frontend: https://staging.federalbills.example.com

**Production:**
- API: https://api.federalbills.example.com/monitoring/health
- Frontend: https://federalbills.example.com

## Performance Optimization

### Caching

**Dependencies:**
- Node.js dependencies cached using `actions/setup-node` cache
- Python dependencies cached using `actions/setup-python` cache

**Docker Layers:**
- Multi-stage builds for smaller images
- Layer caching for faster builds

**Build Artifacts:**
- Production builds cached for 30 days
- Test reports retained for 7 days

### Parallel Jobs

Most CI jobs run in parallel to minimize total runtime:
- Code quality + Tests run simultaneously
- Independent test suites (frontend, API, E2E) run in parallel
- Build verification runs alongside tests

## Troubleshooting

### Failed CI Checks

**Linting Errors:**
```bash
# Fix automatically with pre-commit
pre-commit run --all-files

# Or manually
cd apps/frontend && npm run lint --fix
cd apps/api && black app/ && isort app/
```

**Type Errors:**
```bash
# Frontend
cd apps/frontend && npx tsc --noEmit

# Backend
cd apps/api && mypy app/
```

**Test Failures:**
```bash
# Run tests locally
cd apps/frontend && npm test
cd apps/api && pytest
```

### Failed Deployment

1. **Check logs in GitHub Actions**
2. **Verify secrets are configured**
3. **Check server connectivity:**
   ```bash
   ssh -i ~/.ssh/deploy_key user@server
   ```
4. **Check Docker registry access:**
   ```bash
   docker login docker.io
   ```

### Slow Pipeline

**Identify bottleneck:**
- Check job durations in GitHub Actions
- Look for timeout warnings

**Common causes:**
- E2E tests timing out → Increase `timeout-minutes`
- Docker builds slow → Optimize Dockerfile layers
- Large dependencies → Review package.json/requirements.txt

### Migration Failures

1. **Check migration logs**
2. **Verify database connectivity**
3. **Test migration locally:**
   ```bash
   docker-compose exec api alembic upgrade head
   ```
4. **Rollback if needed:**
   ```bash
   docker-compose exec api alembic downgrade -1
   ```

## Security Best Practices

### Secrets Management
- ✅ Use GitHub Secrets for sensitive data
- ✅ Never commit secrets to repository
- ✅ Rotate secrets regularly
- ✅ Use separate secrets for staging/production

### SSH Keys
- ✅ Use dedicated deploy keys
- ✅ Limit key permissions (read-only where possible)
- ✅ Rotate keys periodically

### Docker Images
- ✅ Scan images for vulnerabilities (Trivy)
- ✅ Use official base images
- ✅ Run as non-root user
- ✅ Keep base images updated

### Access Control
- ✅ Require PR approvals
- ✅ Use environment protection rules
- ✅ Limit who can trigger manual workflows
- ✅ Enable branch protection

## Metrics & KPIs

### Pipeline Health
- **Success Rate:** Target > 95%
- **Mean Time to Build:** < 20 minutes
- **Mean Time to Deploy:** < 30 minutes
- **Rollback Rate:** < 5%

### Test Coverage
- **Frontend:** Target > 80%
- **API:** Target > 85%
- **E2E:** All critical paths covered

### Deployment Frequency
- **Staging:** Daily
- **Production:** Weekly (or as needed)

## Future Improvements

### Planned Enhancements
- [ ] Automated performance testing
- [ ] Visual regression testing
- [ ] Canary deployments
- [ ] Blue-green deployment strategy
- [ ] Automated changelog generation
- [ ] Integration testing with external APIs
- [ ] Database migration preview in PR
- [ ] Automatic dependency updates

### Infrastructure as Code
- [ ] Terraform for cloud resources
- [ ] Kubernetes manifests
- [ ] Helm charts
- [ ] Auto-scaling configuration

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Deployment Guide](./DEPLOYMENT.md)
- [Rate Limiting Documentation](./RATE_LIMITING.md)
