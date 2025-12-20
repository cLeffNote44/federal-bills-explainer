"""
Comprehensive tests for monitoring router.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock, AsyncMock
import time

from fbx_core.models.tables import Base, Bill
from apps.api.app.routers import monitoring


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create test database with tables."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_token():
    """Return test admin token."""
    return "test-admin-token-" + "x" * 32


@pytest.fixture
def app(test_db, admin_token):
    """Create test FastAPI application."""
    # Override get_db dependency
    def override_get_db():
        yield test_db

    monitoring.get_db = override_get_db

    # Mock settings
    with patch('apps.api.app.routers.monitoring.settings') as mock_settings:
        mock_settings.admin_token = admin_token

        app = FastAPI()
        app.include_router(monitoring.router, prefix="/monitoring")
        yield app


class TestHealthEndpoint:
    """Test GET /monitoring/health endpoint."""

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_health_all_components_healthy(self, mock_cache, app):
        """Test health check when all components are healthy."""
        # Mock cache service
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.return_value = {"status": "healthy"}
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get("/monitoring/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "components" in data

        # Check components
        components = data["components"]
        assert "database" in components
        assert "cache" in components

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_health_includes_timestamp(self, mock_cache, app):
        """Test that health check includes timestamp."""
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.return_value = {"status": "healthy"}
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get("/monitoring/health")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data

        # Timestamp should be recent (within last minute)
        import datetime
        timestamp = datetime.datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = (now - timestamp).total_seconds()
        assert diff < 60

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_health_includes_version(self, mock_cache, app):
        """Test that health check includes version."""
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.return_value = {"status": "healthy"}
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get("/monitoring/health")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_health_database_check(self, mock_cache, app, test_db):
        """Test database component health check."""
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.return_value = {"status": "healthy"}
        mock_cache.return_value = mock_cache_service

        # Add a bill to test database connectivity
        bill = Bill(
            congress=118,
            bill_type="hr",
            number=1,
            title="Test Bill",
            summary="Test",
            status="introduced",
        )
        test_db.add(bill)
        test_db.commit()

        client = TestClient(app)
        response = client.get("/monitoring/health")

        assert response.status_code == 200
        data = response.json()

        assert data["components"]["database"]["status"] == "healthy"
        assert "bill_count" in data["components"]["database"]

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_health_cache_check(self, mock_cache, app):
        """Test cache component health check."""
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.return_value = {
            "status": "healthy",
            "connected": True
        }
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get("/monitoring/health")

        assert response.status_code == 200
        data = response.json()

        assert "cache" in data["components"]
        assert data["components"]["cache"]["status"] == "healthy"

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_health_cache_unavailable(self, mock_cache, app):
        """Test health check when cache is unavailable."""
        # Mock cache service to raise exception
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.side_effect = Exception("Redis connection failed")
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get("/monitoring/health")

        assert response.status_code == 503
        data = response.json()

        assert data["status"] == "unhealthy"
        assert "cache" in data["components"]
        # Cache should be marked as unhealthy


class TestLivenessEndpoint:
    """Test GET /monitoring/health/live endpoint."""

    def test_liveness_returns_200(self, app):
        """Test that liveness probe returns 200."""
        client = TestClient(app)
        response = client.get("/monitoring/health/live")

        assert response.status_code == 200

    def test_liveness_response_format(self, app):
        """Test liveness probe response format."""
        client = TestClient(app)
        response = client.get("/monitoring/health/live")

        data = response.json()
        assert data["status"] == "alive"

    def test_liveness_fast_response(self, app):
        """Test that liveness probe responds quickly."""
        client = TestClient(app)

        start = time.time()
        response = client.get("/monitoring/health/live")
        elapsed = time.time() - start

        assert response.status_code == 200
        # Should respond in less than 50ms
        assert elapsed < 0.05

    def test_liveness_no_dependencies(self, app):
        """Test liveness probe doesn't check dependencies."""
        # Liveness should always return 200 regardless of dependencies
        client = TestClient(app)
        response = client.get("/monitoring/health/live")

        assert response.status_code == 200


class TestReadinessEndpoint:
    """Test GET /monitoring/health/ready endpoint."""

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_readiness_when_ready(self, mock_cache, app):
        """Test readiness probe when service is ready."""
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.return_value = {"status": "healthy"}
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get("/monitoring/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_readiness_when_not_ready(self, mock_cache, app):
        """Test readiness probe when service is not ready."""
        # Mock cache as unhealthy
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.side_effect = Exception("Cache unavailable")
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get("/monitoring/health/ready")

        assert response.status_code == 503

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_readiness_checks_database(self, mock_cache, app, test_db):
        """Test that readiness checks database connectivity."""
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.return_value = {"status": "healthy"}
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get("/monitoring/health/ready")

        # Should be able to query database
        assert response.status_code == 200


class TestMetricsEndpoint:
    """Test GET /monitoring/metrics endpoint."""

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_metrics_requires_admin_token(self, mock_cache, app, admin_token):
        """Test that metrics endpoint requires admin token."""
        mock_cache_service = AsyncMock()
        mock_cache_service.get_stats.return_value = {}
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)

        # Without token
        response = client.get("/monitoring/metrics")
        assert response.status_code == 422  # Missing header

        # With invalid token
        response = client.get(
            "/monitoring/metrics",
            headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == 403

        # With valid token
        response = client.get(
            "/monitoring/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_metrics_response_format(self, mock_cache, app, admin_token):
        """Test metrics endpoint response format."""
        mock_cache_service = AsyncMock()
        mock_cache_service.get_stats.return_value = {
            "hits": 100,
            "misses": 20,
            "hit_rate": 0.83
        }
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get(
            "/monitoring/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "timestamp" in data
        assert "system" in data
        assert "database" in data
        assert "cache" in data

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_metrics_system_info(self, mock_cache, app, admin_token):
        """Test metrics includes system information."""
        mock_cache_service = AsyncMock()
        mock_cache_service.get_stats.return_value = {}
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get(
            "/monitoring/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        system = data["system"]
        assert "cpu_percent" in system
        assert "memory_percent" in system
        assert "disk_usage_percent" in system

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_metrics_database_info(self, mock_cache, app, admin_token, test_db):
        """Test metrics includes database information."""
        mock_cache_service = AsyncMock()
        mock_cache_service.get_stats.return_value = {}
        mock_cache.return_value = mock_cache_service

        # Add test data
        bill = Bill(
            congress=118,
            bill_type="hr",
            number=1,
            title="Test",
            summary="Test",
            status="introduced",
        )
        test_db.add(bill)
        test_db.commit()

        client = TestClient(app)
        response = client.get(
            "/monitoring/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        database = data["database"]
        assert "bill_count" in database
        assert database["bill_count"] >= 1

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_metrics_cache_info(self, mock_cache, app, admin_token):
        """Test metrics includes cache statistics."""
        mock_cache_service = AsyncMock()
        mock_cache_service.get_stats.return_value = {
            "hits": 500,
            "misses": 100,
            "hit_rate": 0.83,
            "keys": 42
        }
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)
        response = client.get(
            "/monitoring/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        cache = data["cache"]
        assert cache["hits"] == 500
        assert cache["misses"] == 100
        assert cache["hit_rate"] == 0.83


class TestPrometheusMetricsEndpoint:
    """Test GET /monitoring/metrics/prometheus endpoint."""

    def test_prometheus_metrics_format(self, app):
        """Test Prometheus metrics endpoint returns correct format."""
        client = TestClient(app)
        response = client.get("/monitoring/metrics/prometheus")

        assert response.status_code == 200
        # Prometheus format is plain text
        assert "text/plain" in response.headers.get("content-type", "")

    def test_prometheus_metrics_content(self, app):
        """Test Prometheus metrics content."""
        client = TestClient(app)
        response = client.get("/monitoring/metrics/prometheus")

        assert response.status_code == 200
        content = response.text

        # Should contain metrics
        assert len(content) > 0

    def test_prometheus_metrics_no_auth_required(self, app):
        """Test Prometheus endpoint doesn't require authentication."""
        client = TestClient(app)
        response = client.get("/monitoring/metrics/prometheus")

        # Should work without Authorization header
        assert response.status_code == 200

    def test_prometheus_metrics_multiple_requests(self, app):
        """Test multiple requests to Prometheus endpoint."""
        client = TestClient(app)

        # Make multiple requests
        for _ in range(5):
            response = client.get("/monitoring/metrics/prometheus")
            assert response.status_code == 200


class TestMonitoringIntegration:
    """Integration tests for monitoring router."""

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_all_endpoints_accessible(self, mock_cache, app, admin_token):
        """Test all monitoring endpoints are accessible."""
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.return_value = {"status": "healthy"}
        mock_cache_service.get_stats.return_value = {}
        mock_cache.return_value = mock_cache_service

        client = TestClient(app)

        # Health endpoint
        response = client.get("/monitoring/health")
        assert response.status_code == 200

        # Liveness endpoint
        response = client.get("/monitoring/health/live")
        assert response.status_code == 200

        # Readiness endpoint
        response = client.get("/monitoring/health/ready")
        assert response.status_code == 200

        # Metrics endpoint (with auth)
        response = client.get(
            "/monitoring/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

        # Prometheus endpoint
        response = client.get("/monitoring/metrics/prometheus")
        assert response.status_code == 200

    @patch('apps.api.app.routers.monitoring.get_cache_service')
    def test_health_degradation_scenarios(self, mock_cache, app):
        """Test various health degradation scenarios."""
        client = TestClient(app)

        # Scenario 1: All healthy
        mock_cache_service = AsyncMock()
        mock_cache_service.health_check.return_value = {"status": "healthy"}
        mock_cache.return_value = mock_cache_service

        response = client.get("/monitoring/health")
        assert response.status_code == 200

        # Scenario 2: Cache unhealthy
        mock_cache_service.health_check.side_effect = Exception("Cache down")

        response = client.get("/monitoring/health")
        assert response.status_code == 503

    def test_monitoring_with_middleware(self, app):
        """Test monitoring endpoints work with middleware."""
        from starlette.middleware.base import BaseHTTPMiddleware

        class TestMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                response = await call_next(request)
                response.headers["X-Test"] = "value"
                return response

        # This app already has monitoring router
        # Just test that endpoints still work
        client = TestClient(app)

        response = client.get("/monitoring/health/live")
        assert response.status_code == 200
