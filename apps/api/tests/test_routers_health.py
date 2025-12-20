"""
Comprehensive tests for health router.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.routers import health


@pytest.fixture
def app():
    """Create test FastAPI application."""
    app = FastAPI()
    app.include_router(health.router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestHealthzEndpoint:
    """Test GET /healthz endpoint."""

    def test_healthz_returns_200(self, client):
        """Test that healthz endpoint returns 200 status."""
        response = client.get("/healthz")

        assert response.status_code == 200

    def test_healthz_response_format(self, client):
        """Test healthz response format."""
        response = client.get("/healthz")

        data = response.json()
        assert isinstance(data, dict)
        assert "ok" in data
        assert data["ok"] is True

    def test_healthz_response_type(self, client):
        """Test healthz returns JSON response."""
        response = client.get("/healthz")

        assert response.headers["content-type"] == "application/json"

    def test_healthz_no_authentication_required(self, client):
        """Test that healthz does not require authentication."""
        response = client.get("/healthz")

        assert response.status_code == 200
        # Should not require Authorization header

    def test_healthz_multiple_requests(self, client):
        """Test multiple sequential health check requests."""
        for _ in range(10):
            response = client.get("/healthz")
            assert response.status_code == 200
            assert response.json()["ok"] is True

    def test_healthz_accepts_get_only(self, client):
        """Test that healthz only accepts GET requests."""
        # POST should not be allowed
        response = client.post("/healthz")
        assert response.status_code == 405  # Method Not Allowed

        # PUT should not be allowed
        response = client.put("/healthz")
        assert response.status_code == 405

        # DELETE should not be allowed
        response = client.delete("/healthz")
        assert response.status_code == 405

    def test_healthz_with_query_parameters(self, client):
        """Test healthz ignores query parameters."""
        response = client.get("/healthz?foo=bar&baz=qux")

        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_healthz_with_headers(self, client):
        """Test healthz works with arbitrary headers."""
        response = client.get(
            "/healthz",
            headers={
                "X-Custom-Header": "test-value",
                "User-Agent": "test-agent"
            }
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_healthz_response_time(self, client):
        """Test that healthz responds quickly."""
        import time

        start = time.time()
        response = client.get("/healthz")
        elapsed = time.time() - start

        assert response.status_code == 200
        # Should respond in less than 100ms
        assert elapsed < 0.1

    def test_healthz_idempotent(self, client):
        """Test that healthz is idempotent (same result on repeated calls)."""
        responses = [client.get("/healthz") for _ in range(5)]

        # All responses should be identical
        for response in responses:
            assert response.status_code == 200
            assert response.json() == {"ok": True}


class TestHealthRouterIntegration:
    """Integration tests for health router."""

    def test_health_router_in_application(self):
        """Test health router integrates correctly with FastAPI app."""
        app = FastAPI()
        app.include_router(health.router)

        client = TestClient(app)
        response = client.get("/healthz")

        assert response.status_code == 200

    def test_health_router_with_prefix(self):
        """Test health router works with custom prefix."""
        app = FastAPI()
        app.include_router(health.router, prefix="/api")

        client = TestClient(app)

        # Should work with prefix
        response = client.get("/api/healthz")
        assert response.status_code == 200

        # Should not work without prefix
        response = client.get("/healthz")
        assert response.status_code == 404

    def test_health_router_with_tags(self):
        """Test health router with custom tags."""
        app = FastAPI()
        app.include_router(health.router, tags=["health"])

        client = TestClient(app)
        response = client.get("/healthz")

        assert response.status_code == 200

    def test_health_with_other_routers(self):
        """Test health router coexists with other routers."""
        from fastapi import APIRouter

        app = FastAPI()

        # Add health router
        app.include_router(health.router)

        # Add another router
        other_router = APIRouter()

        @other_router.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        app.include_router(other_router)

        client = TestClient(app)

        # Both should work
        response1 = client.get("/healthz")
        assert response1.status_code == 200

        response2 = client.get("/test")
        assert response2.status_code == 200

    def test_health_router_with_middleware(self):
        """Test health router works correctly with middleware."""
        from starlette.middleware.base import BaseHTTPMiddleware

        class TestMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                response = await call_next(request)
                response.headers["X-Test-Header"] = "test-value"
                return response

        app = FastAPI()
        app.add_middleware(TestMiddleware)
        app.include_router(health.router)

        client = TestClient(app)
        response = client.get("/healthz")

        assert response.status_code == 200
        assert response.headers["X-Test-Header"] == "test-value"
        assert response.json()["ok"] is True


class TestHealthEndpointUseCase:
    """Test health endpoint use cases."""

    def test_kubernetes_liveness_probe(self, client):
        """Test that healthz works as Kubernetes liveness probe."""
        # Kubernetes liveness probes typically just check if service is up
        response = client.get("/healthz")

        assert response.status_code == 200
        # Any 200 response means the service is alive

    def test_load_balancer_health_check(self, client):
        """Test that healthz works for load balancer health checks."""
        # Load balancers need quick, reliable health checks
        for _ in range(20):
            response = client.get("/healthz")
            assert response.status_code == 200

    def test_monitoring_system_integration(self, client):
        """Test that healthz works for monitoring systems."""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()

        # Monitoring systems expect consistent response format
        assert "ok" in data
        assert isinstance(data["ok"], bool)

    def test_uptime_monitoring(self, client):
        """Test healthz for uptime monitoring services."""
        import time

        # Simulate uptime monitoring making requests at intervals
        for _ in range(5):
            response = client.get("/healthz")
            assert response.status_code == 200
            time.sleep(0.01)  # 10ms between checks

    def test_health_check_during_high_load(self, client):
        """Test health check responds correctly under load."""
        import concurrent.futures

        def make_request():
            response = client.get("/healthz")
            return response.status_code

        # Simulate concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 50
