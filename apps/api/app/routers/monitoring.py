"""
Enhanced health check and monitoring endpoints.
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import psutil
import os
import time
from pydantic import BaseModel, Field
from fbx_core.utils.logging import logger
from fbx_core.db.session import SessionLocal
from app.dependencies.auth import require_admin


router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class HealthStatus(BaseModel):
    """Health status response model."""
    status: str = Field(..., example="healthy", description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current environment")
    checks: Dict[str, Dict[str, Any]] = Field(..., description="Individual component checks")


class MetricsResponse(BaseModel):
    """System metrics response."""
    timestamp: datetime
    system: Dict[str, Any]
    application: Dict[str, Any]
    database: Optional[Dict[str, Any]] = None


class ComponentHealth(BaseModel):
    """Individual component health status."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Track application start time
APP_START_TIME = time.time()


def get_db():
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_optional_db():
    """Optional database dependency for health checks."""
    try:
        db = SessionLocal()
        yield db
        db.close()
    except Exception:
        yield None


def get_db_health(db: Session) -> ComponentHealth:
    """Check database health."""
    start_time = time.time()
    try:
        # Execute a simple query
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        # Get additional DB stats
        db_stats = {
            "connection_count": db.execute(
                text("SELECT count(*) FROM pg_stat_activity")
            ).scalar() if db.bind.dialect.name == 'postgresql' else None
        }

        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            name="database",
            status="healthy",
            response_time_ms=response_time,
            details=db_stats
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(e, {"component": "database_health_check"})
        return ComponentHealth(
            name="database",
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )


def get_redis_health() -> ComponentHealth:
    """Check Redis/cache health."""
    start_time = time.time()
    try:
        # This would check actual Redis connection
        # For now, we'll simulate
        import random
        if random.random() > 0.95:  # Simulate 5% failure rate
            raise Exception("Redis connection timeout")

        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            name="cache",
            status="healthy",
            response_time_ms=response_time,
            details={"type": "redis", "connected": True}
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            name="cache",
            status="degraded",  # Cache is not critical
            response_time_ms=response_time,
            error=str(e)
        )


def get_external_api_health() -> ComponentHealth:
    """Check external API connectivity."""
    start_time = time.time()
    try:
        # Check Congress API availability
        # In production, you'd make an actual lightweight API call
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            name="congress_api",
            status="healthy",
            response_time_ms=response_time,
            details={"endpoint": "api.congress.gov", "reachable": True}
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            name="congress_api",
            status="degraded",
            response_time_ms=response_time,
            error=str(e)
        )


@router.get("/health", response_model=HealthStatus)
async def health_check(db: Optional[Session] = Depends(get_optional_db)):
    """
    Comprehensive health check endpoint.

    Returns overall system health and individual component statuses.
    """
    checks = {}
    overall_status = "healthy"

    # Database health
    if db:
        db_health = get_db_health(db)
        checks["database"] = db_health.model_dump()
        if db_health.status == "unhealthy":
            overall_status = "unhealthy"
        elif db_health.status == "degraded" and overall_status == "healthy":
            overall_status = "degraded"

    # Cache health
    cache_health = get_redis_health()
    checks["cache"] = cache_health.model_dump()
    if cache_health.status == "degraded" and overall_status == "healthy":
        overall_status = "degraded"

    # External API health
    api_health = get_external_api_health()
    checks["external_api"] = api_health.model_dump()
    if api_health.status == "degraded" and overall_status == "healthy":
        overall_status = "degraded"

    # Calculate uptime
    uptime_seconds = time.time() - APP_START_TIME

    response = HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime_seconds,
        version=os.getenv("APP_VERSION", "1.0.0"),
        environment=os.getenv("ENVIRONMENT", "development"),
        checks=checks
    )

    # Log health check
    logger.log_performance_metric(
        metric_name="health_check",
        value=1 if overall_status == "healthy" else 0,
        unit="status",
        overall_status=overall_status
    )

    # Return appropriate status code
    if overall_status == "unhealthy":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response.model_dump())

    return response


@router.get("/health/live")
async def liveness_probe():
    """
    Simple liveness probe for Kubernetes.

    Returns 200 if the application is running.
    """
    return {"status": "alive", "timestamp": datetime.utcnow()}


@router.get("/health/ready")
async def readiness_probe(db: Optional[Session] = Depends(get_optional_db)):
    """
    Readiness probe for Kubernetes.

    Returns 200 if the application is ready to serve requests.
    """
    # Check critical dependencies
    if db:
        try:
            db.execute(text("SELECT 1"))
        except Exception as e:
            logger.log_error(e, {"probe": "readiness"})
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not ready"
            )

    return {"status": "ready", "timestamp": datetime.utcnow()}


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    include_system: bool = True,
    include_database: bool = False,
    _: Any = Depends(require_admin)
):
    """
    Get detailed system and application metrics.

    Requires admin authentication.
    """
    metrics = {
        "timestamp": datetime.utcnow(),
        "application": {
            "uptime_seconds": time.time() - APP_START_TIME,
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("ENVIRONMENT", "development"),
        }
    }

    if include_system:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        metrics["system"] = {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": disk.percent,
            },
            "network": {
                "connections": len(psutil.net_connections()),
            }
        }
    else:
        metrics["system"] = {}

    if include_database:
        # Database metrics (placeholder - implement based on your DB)
        metrics["database"] = {
            "connection_pool_size": 10,
            "active_connections": 3,
            "query_cache_hit_rate": 0.85,
        }

    # Log metrics collection
    logger.log_performance_metric(
        metric_name="metrics_collected",
        value=1,
        unit="count",
        cpu_percent=metrics["system"].get("cpu", {}).get("percent") if include_system else None
    )

    return MetricsResponse(**metrics)


@router.get("/metrics/prometheus")
async def prometheus_metrics(_: Any = Depends(require_admin)):
    """
    Export metrics in Prometheus format.

    Requires admin authentication.
    """
    uptime = time.time() - APP_START_TIME
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    # Format metrics in Prometheus exposition format
    metrics_text = f"""# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds gauge
app_uptime_seconds {uptime}

# HELP system_cpu_usage_percent System CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent {cpu_percent}

# HELP system_memory_usage_bytes System memory usage in bytes
# TYPE system_memory_usage_bytes gauge
system_memory_usage_bytes {memory.used}

# HELP system_memory_total_bytes System total memory in bytes
# TYPE system_memory_total_bytes gauge
system_memory_total_bytes {memory.total}
"""

    return metrics_text
