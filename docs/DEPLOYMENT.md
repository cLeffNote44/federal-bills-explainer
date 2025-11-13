# Deployment Guide

This guide covers deploying the Federal Bills Explainer application to production and staging environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Infrastructure Setup](#infrastructure-setup)
- [Environment Configuration](#environment-configuration)
- [Deployment Methods](#deployment-methods)
- [Database Migrations](#database-migrations)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Rollback Procedures](#rollback-procedures)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- Docker (v24.0+) and Docker Compose (v2.20+)
- Git
- PostgreSQL client (for database operations)
- OpenSSL (for generating secrets)

### Required Accounts & Access

- GitHub repository access
- Docker Hub or container registry account
- Cloud provider account (AWS, GCP, Azure, DigitalOcean, etc.)
- Domain name and DNS access
- SSL/TLS certificate (Let's Encrypt recommended)

## Infrastructure Setup

### 1. Server Requirements

**Staging Environment:**
- 2 CPU cores
- 4 GB RAM
- 40 GB SSD storage
- Ubuntu 22.04 LTS or similar

**Production Environment:**
- 4+ CPU cores
- 8+ GB RAM
- 100+ GB SSD storage
- Ubuntu 22.04 LTS or similar

### 2. Install Docker

```bash
# Update packages
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 3. Setup Application Directory

```bash
# Create directory
sudo mkdir -p /opt/federal-bills-explainer
sudo chown $USER:$USER /opt/federal-bills-explainer
cd /opt/federal-bills-explainer

# Clone repository
git clone https://github.com/yourusername/federal-bills-explainer.git .
```

## Environment Configuration

### 1. Generate Secrets

```bash
# Generate JWT secret (32 bytes)
openssl rand -hex 32

# Generate admin token (32 bytes)
openssl rand -hex 32

# Generate database password (32 bytes)
openssl rand -hex 32
```

### 2. Create Environment File

Create `.env` file in the project root:

```bash
# Database Configuration
DB_USER=federal_bills
DB_PASSWORD=<generated-password>
DB_NAME=federal_bills
DB_PORT=5432

# Redis Configuration
REDIS_PORT=6379

# API Configuration
API_PORT=8000
JWT_SECRET_KEY=<generated-jwt-secret>
ADMIN_TOKEN=<generated-admin-token>
CONGRESS_API_KEY=<your-congress-api-key>
OPENAI_API_KEY=<your-openai-api-key>

# Environment
ENVIRONMENT=production

# Frontend Configuration
FRONTEND_PORT=3000
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
GRAFANA_USER=admin
GRAFANA_PASSWORD=<secure-password>

# Nginx
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443

# Optional: pgAdmin
PGADMIN_EMAIL=admin@yourdomain.com
PGADMIN_PASSWORD=<secure-password>
PGADMIN_PORT=5050

# Logging
LOG_LEVEL=INFO

# Features
EMBEDDINGS_ENABLED=true
EXPLANATIONS_ENABLED=true
```

### 3. Configure Domain & SSL

**Using Let's Encrypt (Recommended):**

```bash
# Install certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Certificates will be saved to:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

Update Nginx configuration to use SSL certificates.

## Deployment Methods

### Method 1: Docker Compose (Recommended for Single Server)

```bash
cd /opt/federal-bills-explainer

# Pull latest code
git pull origin main

# Build and start services
docker-compose up -d --build

# Check logs
docker-compose logs -f

# Verify services are running
docker-compose ps
```

### Method 2: GitHub Actions Automated Deployment

#### Setup GitHub Secrets

Go to `Settings > Secrets and variables > Actions` and add:

```
STAGING_HOST=staging.yourdomain.com
STAGING_USER=deploy
STAGING_SSH_KEY=<private-key>
STAGING_DATABASE_URL=postgresql://user:pass@host:5432/db

PRODUCTION_HOST=yourdomain.com
PRODUCTION_USER=deploy
PRODUCTION_SSH_KEY=<private-key>
PRODUCTION_DATABASE_URL=postgresql://user:pass@host:5432/db

DOCKER_REGISTRY=docker.io
DOCKER_USERNAME=<username>
DOCKER_PASSWORD=<password>

SLACK_WEBHOOK_URL=<webhook-url> (optional)
```

#### Trigger Deployment

**Staging (Automatic):**
- Push to `develop` branch triggers staging deployment automatically

**Production (Manual):**
```bash
# Create a version tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Or use GitHub Actions UI to manually trigger deployment
```

### Method 3: Manual Deployment

```bash
# 1. Build Docker images
docker build -t federal-bills-api:latest -f apps/api/Dockerfile .
docker build -t federal-bills-frontend:latest -f apps/frontend/Dockerfile .

# 2. Push to registry
docker push your-registry/federal-bills-api:latest
docker push your-registry/federal-bills-frontend:latest

# 3. Pull on server
ssh user@server
docker pull your-registry/federal-bills-api:latest
docker pull your-registry/federal-bills-frontend:latest

# 4. Restart services
docker-compose down
docker-compose up -d
```

## Database Migrations

### Running Migrations

**Automatic (on deployment):**
Migrations run automatically when API container starts.

**Manual:**

```bash
# Enter API container
docker-compose exec api bash

# Check current migration status
alembic current

# View migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Upgrade to specific version
alembic upgrade abc123
```

### Creating New Migrations

```bash
# Enter API container
docker-compose exec api bash

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column to bills table"

# Create empty migration
alembic revision -m "Custom migration"

# Edit migration file at: apps/api/alembic/versions/<id>_<message>.py
```

### Migration Best Practices

1. **Always backup before migrations:**
```bash
docker exec federal-bills-postgres pg_dump -U postgres federal_bills > backup_$(date +%Y%m%d_%H%M%S).sql
```

2. **Test migrations on staging first**

3. **Review auto-generated migrations carefully**

4. **Make migrations reversible (implement downgrade)**

5. **For large tables, consider:**
   - Creating indexes concurrently
   - Batching data migrations
   - Using separate maintenance windows

## Monitoring & Health Checks

### Health Check Endpoints

```bash
# API Health
curl http://localhost:8000/monitoring/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z"
}

# Frontend Health
curl http://localhost:3000

# Prometheus Metrics
curl http://localhost:8000/monitoring/metrics/prometheus
```

### Accessing Monitoring Dashboards

- **Grafana**: http://yourdomain.com:3001
  - Default login: admin / (password from .env)
  - Pre-configured dashboards for API metrics

- **Prometheus**: http://yourdomain.com:9090
  - Query metrics directly
  - View targets and alerts

### Log Locations

```bash
# API logs
docker-compose logs api

# Frontend logs
docker-compose logs frontend

# Database logs
docker-compose logs postgres

# Nginx logs
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f --tail=100

# Save logs to file
docker-compose logs --no-color > logs_$(date +%Y%m%d).txt
```

## Rollback Procedures

### Quick Rollback (Docker)

```bash
# Find latest backup
LATEST_BACKUP=$(ls -t /opt/backups/ | head -1)

# Stop current deployment
docker-compose down

# Restore database
docker exec -i federal-bills-postgres psql -U postgres federal_bills < /opt/backups/$LATEST_BACKUP/database.sql

# Revert to previous image version
docker-compose pull --ignore-pull-failures
docker-compose up -d
```

### Rollback Using GitHub Actions

1. Go to Actions tab in GitHub
2. Find the "Deploy to Production" workflow
3. Look at the "rollback" job
4. Manually trigger rollback if needed

### Rollback Database Migration

```bash
# Enter API container
docker-compose exec api bash

# Downgrade to previous version
alembic downgrade -1

# Or downgrade to specific version
alembic downgrade <revision-id>

# Verify
alembic current
```

## Zero-Downtime Deployment

For production deployments with zero downtime:

```bash
# 1. Start new version alongside old version
docker-compose up -d --no-deps --scale api=2 --no-recreate api

# 2. Wait for health check
sleep 10

# 3. Remove old version
docker-compose up -d --no-deps --scale api=1 --remove-orphans api

# 4. Repeat for frontend
docker-compose up -d --no-deps --scale frontend=2 --no-recreate frontend
sleep 10
docker-compose up -d --no-deps --scale frontend=1 --remove-orphans frontend
```

## Backup & Restore

### Automated Backups

Create a cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/federal-bills-explainer/scripts/backup.sh
```

**backup.sh:**
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/federal-bills-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup database
docker exec federal-bills-postgres pg_dump -U postgres federal_bills > $BACKUP_DIR/database.sql

# Backup environment config
cp /opt/federal-bills-explainer/.env $BACKUP_DIR/.env

# Compress backup
tar -czf $BACKUP_DIR.tar.gz -C $(dirname $BACKUP_DIR) $(basename $BACKUP_DIR)
rm -rf $BACKUP_DIR

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR.tar.gz s3://your-bucket/backups/

# Keep only last 7 days of backups
find /opt/backups -name "*.tar.gz" -mtime +7 -delete
```

### Manual Restore

```bash
# Extract backup
tar -xzf backup_20240101-120000.tar.gz

# Restore database
docker exec -i federal-bills-postgres psql -U postgres federal_bills < backup_20240101-120000/database.sql

# Restart services
docker-compose restart
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Check container status
docker-compose ps

# Restart specific service
docker-compose restart <service-name>

# Force recreate
docker-compose up -d --force-recreate <service-name>
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U postgres -d federal_bills -c "SELECT 1"

# Check DATABASE_URL in API container
docker-compose exec api env | grep DATABASE_URL
```

### High Memory Usage

```bash
# Check container resource usage
docker stats

# Restart services to clear memory
docker-compose restart

# Check for memory leaks in logs
docker-compose logs | grep -i "memory\|oom"
```

### SSL Certificate Issues

```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Test certificate renewal
sudo certbot renew --dry-run

# Reload Nginx
docker-compose exec nginx nginx -s reload
```

### Performance Issues

1. Check database indexes: See `infra/database/optimizations.sql`
2. Check Redis cache hit rate
3. Review API logs for slow queries
4. Check Grafana dashboards for metrics

## Security Checklist

- [ ] All secrets are stored securely (not in git)
- [ ] Database has strong password
- [ ] JWT secret is randomly generated and secure
- [ ] SSL/TLS certificates are valid
- [ ] Firewall is configured (only 80, 443 open publicly)
- [ ] SSH key-based authentication only
- [ ] Regular security updates applied
- [ ] Backups are tested and working
- [ ] Rate limiting is enabled
- [ ] CORS origins are configured correctly
- [ ] Admin endpoints are protected

## Performance Tuning

### Database

```sql
-- Adjust shared_buffers (25% of RAM)
ALTER SYSTEM SET shared_buffers = '2GB';

-- Adjust work_mem
ALTER SYSTEM SET work_mem = '64MB';

-- Reload configuration
SELECT pg_reload_conf();
```

### API

```python
# Adjust worker count in Dockerfile
CMD ["uvicorn", "app.main:app", "--workers", "4", "--host", "0.0.0.0"]

# Workers = (2 x CPU cores) + 1
```

### Frontend

```bash
# Build with optimizations
NODE_ENV=production npm run build
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/federal-bills-explainer/issues
- Documentation: https://docs.federalbills.example.com
- Email: support@federalbills.example.com
