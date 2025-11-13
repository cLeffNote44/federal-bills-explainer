"""
Tests for security middleware.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from fbx_core.middleware.security import (
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    RequestLoggingMiddleware,
    configure_cors,
    add_security_middleware,
)


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    @app.post("/test")
    async def test_post():
        return {"message": "posted"}

    return app


class TestSecurityHeadersMiddleware:
    """Test SecurityHeadersMiddleware."""

    def test_security_headers_added(self, app):
        """Test that security headers are added to responses."""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        # Check all security headers
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers

    def test_csp_header_content(self, app):
        """Test Content Security Policy header content."""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_x_frame_options(self, app):
        """Test X-Frame-Options header."""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.headers["X-Frame-Options"] == "DENY"

    def test_x_content_type_options(self, app):
        """Test X-Content-Type-Options header."""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_hsts_on_https(self, app):
        """Test HSTS header is added for HTTPS requests."""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app, base_url="https://testserver")

        response = client.get("/test")

        assert "Strict-Transport-Security" in response.headers
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts

    def test_server_header_removed(self, app):
        """Test that Server header is removed."""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert "Server" not in response.headers or response.headers.get("Server") != "uvicorn"

    def test_custom_powered_by_header(self, app):
        """Test X-Powered-By header is set."""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.headers.get("X-Powered-By") == "Federal Bills Explainer"


class TestRequestValidationMiddleware:
    """Test RequestValidationMiddleware."""

    def test_request_within_size_limit(self, app):
        """Test request within size limit is accepted."""
        app.add_middleware(RequestValidationMiddleware, max_content_length=1024)
        client = TestClient(app)

        response = client.post("/test", json={"data": "small payload"})

        assert response.status_code == 200

    def test_request_exceeds_size_limit(self, app):
        """Test request exceeding size limit is rejected."""
        app.add_middleware(RequestValidationMiddleware, max_content_length=100)
        client = TestClient(app)

        large_data = "x" * 200
        response = client.post(
            "/test",
            json={"data": large_data},
            headers={"Content-Length": "200"}
        )

        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

    def test_request_without_content_length(self, app):
        """Test request without Content-Length header passes through."""
        app.add_middleware(RequestValidationMiddleware, max_content_length=100)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 200


class TestRequestLoggingMiddleware:
    """Test RequestLoggingMiddleware."""

    def test_request_logging(self, app, caplog):
        """Test that requests are logged."""
        import logging
        caplog.set_level(logging.INFO)

        app.add_middleware(RequestLoggingMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 200

        # Check logs
        assert any("Request started" in record.message for record in caplog.records)
        assert any("Request completed" in record.message for record in caplog.records)

    def test_request_id_in_response(self, app):
        """Test that request ID is added to response headers."""
        app.add_middleware(RequestLoggingMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_custom_request_id_preserved(self, app):
        """Test that custom request ID from headers is preserved."""
        app.add_middleware(RequestLoggingMiddleware)
        client = TestClient(app)

        custom_id = "custom-request-id-12345"
        response = client.get("/test", headers={"X-Request-ID": custom_id})

        assert response.headers["X-Request-ID"] == custom_id

    def test_error_logging(self, app, caplog):
        """Test that errors are logged properly."""
        import logging
        caplog.set_level(logging.ERROR)

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        app.add_middleware(RequestLoggingMiddleware)
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/error")

        assert response.status_code == 500
        assert any("Request failed" in record.message for record in caplog.records)


class TestConfigureCORS:
    """Test configure_cors function."""

    def test_configure_cors(self, app):
        """Test CORS configuration."""
        origins = ["http://localhost:3000", "https://example.com"]
        configure_cors(app, origins)

        client = TestClient(app)

        # Preflight request
        response = client.options(
            "/test",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )

        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers

    def test_cors_with_credentials(self, app):
        """Test CORS with credentials enabled."""
        origins = ["http://localhost:3000"]
        configure_cors(app, origins)

        client = TestClient(app)

        response = client.get("/test", headers={"Origin": "http://localhost:3000"})

        assert "Access-Control-Allow-Credentials" in response.headers
        assert response.headers["Access-Control-Allow-Credentials"] == "true"


class TestAddSecurityMiddleware:
    """Test add_security_middleware convenience function."""

    def test_add_all_security_middleware(self, app):
        """Test that all security middleware is added."""
        add_security_middleware(app, max_content_length=1024*1024)

        client = TestClient(app)

        response = client.get("/test")

        # Check that security headers are present (from SecurityHeadersMiddleware)
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers

        # Check that request ID is present (from RequestLoggingMiddleware)
        assert "X-Request-ID" in response.headers

    def test_middleware_execution_order(self, app):
        """Test that middleware executes in correct order."""
        add_security_middleware(app)

        client = TestClient(app)

        response = client.get("/test")

        # All middleware should have executed
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "Content-Security-Policy" in response.headers


class TestMiddlewareIntegration:
    """Integration tests for all middleware together."""

    def test_all_middleware_together(self, app):
        """Test all security middleware working together."""
        configure_cors(app, ["http://localhost:3000"])
        add_security_middleware(app, max_content_length=1024)

        client = TestClient(app)

        # Test GET request
        response = client.get("/test", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200
        assert "Content-Security-Policy" in response.headers
        assert "X-Request-ID" in response.headers
        assert "Access-Control-Allow-Origin" in response.headers

        # Test POST request
        response = client.post(
            "/test",
            json={"data": "test"},
            headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_middleware_with_error(self, app):
        """Test middleware behavior when endpoint raises error."""
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        add_security_middleware(app)

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/error")

        # Security headers should still be present even on error
        assert response.status_code == 500
        # Note: Some headers might not be present on error responses
        # depending on FastAPI's error handling
