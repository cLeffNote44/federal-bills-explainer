# Deployment Guide - Federal Bills Explainer

## 🚀 Staging Deployment

This guide covers deploying the Federal Bills Explainer to a staging environment.

---

## Prerequisites

### Required Services
- PostgreSQL 16+ with pgvector extension
- Redis 7+ (for caching and rate limiting)
- Docker & Docker Compose (recommended) OR Kubernetes cluster
- Domain name with SSL certificate (for production)

### Required Credentials
- Congress.gov API Key: https://api.congress.gov/sign-up/
- Strong JWT secret (generate with `openssl rand -hex 32`)
- Strong admin token (generate with `openssl rand -hex 32`)
- Database credentials
- SSL/TLS certificates (for HTTPS)

---

## Deployment Options

### Option 1: Docker Compose (Recommended for Staging)

#### 1. Prepare Environment

```bash
# Clone repository
git clone https://github.com/cLeffNote44/federal-bills-explainer.git
cd federal-bills-explainer

# Create environment file
cp .env.example .env
```

#### 2. Configure Environment Variables

Edit `.env` with production values:

```bash
# Database (use strong passwords!)
DB_USER=fbx_prod_user
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME=federal_bills_prod

# API Keys
CONGRESS_API_KEY=your-congress-api-key-here
JWT_SECRET_KEY=$(openssl rand -hex 32)
ADMIN_TOKEN=$(openssl rand -hex 32)

# URLs
CORS_ORIGINS=https://your-staging-domain.com
NEXT_PUBLIC_API_BASE_URL=https://api.your-staging-domain.com

# Environment
ENVIRONMENT=staging
LOG_LEVEL=INFO
DRY_RUN=false

# Features
EMBEDDINGS_ENABLED=true
EXPLANATIONS_ENABLED=true

# Redis
REDIS_URL=redis://redis:6379/0

# Security
MAX_REQUEST_SIZE=10485760
SESSION_TIMEOUT=3600
FORCE_HTTPS=true
```

#### 3. Build and Deploy

```bash
# Build images
docker compose build

# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

#### 4. Initialize Database

```bash
# Run migrations
docker compose exec api alembic upgrade head

# Verify database
docker compose exec db psql -U $DB_USER -d $DB_NAME -c "\dt"
```

#### 5. Initial Data Ingestion

```bash
# Test with sample bill first
docker compose run ingestion python -m fbx_ingest.cli sync \
  --dry-run --sample-bill 118-hr-1

# If successful, run full ingestion
docker compose run ingestion python -m fbx_ingest.cli sync --no-dry-run
```

#### 6. Verify Deployment

```bash
# Check API health
curl https://api.your-staging-domain.com/monitoring/health

# Check frontend
curl https://your-staging-domain.com

# Test API endpoint
curl https://api.your-staging-domain.com/bills
```

---

### Option 2: Kubernetes Deployment

#### 1. Prepare Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace federal-bills-explainer

# Create secrets
kubectl create secret generic fbx-secrets \
  --from-literal=db-password=$(openssl rand -base64 32) \
  --from-literal=jwt-secret=$(openssl rand -hex 32) \
  --from-literal=admin-token=$(openssl rand -hex 32) \
  --from-literal=congress-api-key=your-api-key \
  -n federal-bills-explainer

# Create TLS secret (if using HTTPS)
kubectl create secret tls fbx-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n federal-bills-explainer
```

#### 2. Update Kubernetes Manifests

Edit `infra/k8s/overlays/staging/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: federal-bills-explainer

resources:
  - ../../base

configMapGenerator:
  - name: fbx-config
    literals:
      - ENVIRONMENT=staging
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=https://staging.example.com
      - EMBEDDINGS_ENABLED=true

images:
  - name: fbx-api
    newName: your-registry/fbx-api
    newTag: staging-latest
  - name: fbx-frontend
    newName: your-registry/fbx-frontend
    newTag: staging-latest
  - name: fbx-ingestion
    newName: your-registry/fbx-ingestion
    newTag: staging-latest
```

#### 3. Deploy to Kubernetes

```bash
# Build and push images
docker build -t your-registry/fbx-api:staging-latest -f apps/api/Dockerfile .
docker push your-registry/fbx-api:staging-latest

docker build -t your-registry/fbx-frontend:staging-latest -f apps/frontend/Dockerfile apps/frontend
docker push your-registry/fbx-frontend:staging-latest

docker build -t your-registry/fbx-ingestion:staging-latest -f apps/ingestion/Dockerfile .
docker push your-registry/fbx-ingestion:staging-latest

# Apply manifests
kubectl apply -k infra/k8s/overlays/staging

# Check deployment status
kubectl get pods -n federal-bills-explainer
kubectl get services -n federal-bills-explainer
kubectl get ingress -n federal-bills-explainer

# View logs
kubectl logs -f deployment/fbx-api -n federal-bills-explainer
```

#### 4. Run Database Migrations

```bash
# Create migration job or exec into API pod
kubectl exec -it deployment/fbx-api -n federal-bills-explainer -- \
  alembic upgrade head
```

#### 5. Set Up Ingestion CronJob

```yaml
# infra/k8s/base/cronjob-ingestion.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: fbx-ingestion
spec:
  schedule: "0 2 * * *"  # Run daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: ingestion
            image: fbx-ingestion:latest
            command: ["python", "-m", "fbx_ingest.cli", "sync", "--no-dry-run"]
            envFrom:
            - secretRef:
                name: fbx-secrets
            - configMapRef:
                name: fbx-config
          restartPolicy: OnFailure
```

---

## Monitoring Setup

### 1. Prometheus

```yaml
# infra/monitoring/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    scrape_configs:
      - job_name: 'federal-bills-api'
        kubernetes_sd_configs:
        - role: pod
          namespaces:
            names:
            - federal-bills-explainer
        relabel_configs:
        - source_labels: [__meta_kubernetes_pod_label_app]
          regex: fbx-api
          action: keep
        - source_labels: [__meta_kubernetes_pod_ip]
          target_label: __address__
          replacement: ${1}:8000
```

### 2. Grafana Dashboard

Import dashboard from `infra/monitoring/grafana-dashboards/api-dashboard.json`

Key metrics to monitor:
- Request rate and latency
- Error rate
- Cache hit ratio
- Database query performance
- Rate limit hits
- Active connections

### 3. Alerting Rules

```yaml
# infra/monitoring/alert-rules.yaml
groups:
  - name: api_alerts
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value }} requests/sec"

    - alert: APIDown
      expr: up{job="federal-bills-api"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "API is down"
        description: "API has been down for more than 1 minute"
```

---

## Security Checklist

### Pre-Deployment

- [ ] All secrets generated with strong random values
- [ ] No default passwords in use
- [ ] SSL/TLS certificates configured
- [ ] CORS configured for production domains only
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Database backups configured
- [ ] Log aggregation set up
- [ ] Monitoring and alerting configured

### Post-Deployment

- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] Health checks responding
- [ ] API documentation accessible
- [ ] Rate limiting working (test with curl)
- [ ] Authentication working
- [ ] Database connections secure
- [ ] Logs showing no errors
- [ ] Metrics being collected

---

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker compose exec db pg_dump -U $DB_USER $DB_NAME > backup.sql

# Or for Kubernetes
kubectl exec -it deployment/fbx-db -n federal-bills-explainer -- \
  pg_dump -U postgres federal_bills > backup.sql

# Automated daily backups (add to cron)
0 3 * * * /path/to/backup-script.sh
```

### Restore from Backup

```bash
# Docker Compose
docker compose exec -T db psql -U $DB_USER $DB_NAME < backup.sql

# Kubernetes
kubectl exec -i deployment/fbx-db -n federal-bills-explainer -- \
  psql -U postgres federal_bills < backup.sql
```

---

## Scaling Considerations

### Horizontal Scaling

```yaml
# Scale API replicas
kubectl scale deployment fbx-api --replicas=3 -n federal-bills-explainer

# Or use HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fbx-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fbx-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Database Optimization

```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_status ON bills(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_date ON bills(introduced_date);

-- Vacuum and analyze
VACUUM ANALYZE bills;
VACUUM ANALYZE explanations;
```

---

## Troubleshooting

### API Not Responding

```bash
# Check logs
docker compose logs api
# or
kubectl logs -f deployment/fbx-api -n federal-bills-explainer

# Check health endpoint
curl http://localhost:8000/monitoring/health

# Check environment variables
docker compose exec api env | grep FBX_
```

### Database Connection Issues

```bash
# Test database connection
docker compose exec api python -c "from fbx_core.db.session import engine; engine.connect()"

# Check PostgreSQL logs
docker compose logs db
```

### Redis Connection Issues

```bash
# Test Redis connection
docker compose exec redis redis-cli ping

# Check Redis logs
docker compose logs redis
```

### Rate Limiting Not Working

```bash
# Check Redis is accessible
docker compose exec api python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"

# Check rate limit configuration in logs
docker compose logs api | grep -i "rate"
```

---

## Rollback Procedure

```bash
# Docker Compose
docker compose down
git checkout <previous-commit>
docker compose up -d

# Kubernetes
kubectl rollout undo deployment/fbx-api -n federal-bills-explainer
kubectl rollout status deployment/fbx-api -n federal-bills-explainer
```

---

## Support

For deployment issues:
- Email: cLeffNote44@pm.me
- GitHub Issues: https://github.com/cLeffNote44/federal-bills-explainer/issues
- Documentation: See IMPLEMENTATION_GUIDE.md

---

**Last Updated:** 2025-11-09
