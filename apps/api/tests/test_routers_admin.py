"""
Comprehensive tests for admin router.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

from fbx_core.models.tables import Base
from apps.api.app.routers import admin


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

    admin.get_db = override_get_db

    # Mock settings to use test admin token
    with patch('apps.api.app.routers.admin.settings') as mock_settings:
        mock_settings.admin_token = admin_token

        app = FastAPI()
        app.include_router(admin.router, prefix="/admin")
        yield app


class TestTriggerIngestion:
    """Test POST /admin/ingest endpoint."""

    @patch('apps.api.app.routers.admin.IngestionService')
    @patch('apps.api.app.routers.admin.CongressGovProvider')
    def test_successful_ingestion(self, mock_provider, mock_service, app, admin_token):
        """Test successful ingestion with valid admin token."""
        # Mock ingestion service
        mock_service_instance = MagicMock()
        mock_service_instance.run.return_value = 42
        mock_service.return_value = mock_service_instance

        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "42" in data["message"]
        assert "Ingested" in data["message"]

        # Verify service was called
        mock_service_instance.run.assert_called_once()

    @patch('apps.api.app.routers.admin.IngestionService')
    @patch('apps.api.app.routers.admin.CongressGovProvider')
    def test_ingestion_with_bearer_prefix(self, mock_provider, mock_service, app, admin_token):
        """Test ingestion works with Bearer prefix in token."""
        mock_service_instance = MagicMock()
        mock_service_instance.run.return_value = 10
        mock_service.return_value = mock_service_instance

        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    @patch('apps.api.app.routers.admin.IngestionService')
    @patch('apps.api.app.routers.admin.CongressGovProvider')
    def test_ingestion_without_bearer_prefix(self, mock_provider, mock_service, app, admin_token):
        """Test ingestion works without Bearer prefix."""
        mock_service_instance = MagicMock()
        mock_service_instance.run.return_value = 10
        mock_service.return_value = mock_service_instance

        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": admin_token}
        )

        assert response.status_code == 200

    def test_ingestion_with_invalid_token(self, app):
        """Test ingestion fails with invalid admin token."""
        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 403
        assert "Forbidden" in response.json()["detail"]

    def test_ingestion_with_missing_token(self, app):
        """Test ingestion fails with missing authorization header."""
        client = TestClient(app)

        response = client.post("/admin/ingest")

        assert response.status_code == 422  # Validation error

    def test_ingestion_with_empty_token(self, app):
        """Test ingestion fails with empty token."""
        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": ""}
        )

        assert response.status_code == 403

    @patch('apps.api.app.routers.admin.IngestionService')
    @patch('apps.api.app.routers.admin.CongressGovProvider')
    def test_provider_initialization(self, mock_provider, mock_service, app, admin_token):
        """Test that CongressGovProvider is initialized with correct fixtures path."""
        mock_service_instance = MagicMock()
        mock_service_instance.run.return_value = 5
        mock_service.return_value = mock_service_instance

        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

        # Verify provider was initialized with correct fixtures directory
        mock_provider.assert_called_once_with(fixtures_dir="/app/apps/ingestion/fixtures")

    @patch('apps.api.app.routers.admin.IngestionService')
    @patch('apps.api.app.routers.admin.CongressGovProvider')
    def test_service_initialization(self, mock_provider, mock_service, app, admin_token, test_db):
        """Test that IngestionService is initialized with provider and db."""
        mock_service_instance = MagicMock()
        mock_service_instance.run.return_value = 5
        mock_service.return_value = mock_service_instance

        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

        # Verify service was initialized with provider and db session
        mock_service.assert_called_once()
        call_args = mock_service.call_args
        assert call_args[0][1] == test_db  # Second arg is db session

    @patch('apps.api.app.routers.admin.IngestionService')
    @patch('apps.api.app.routers.admin.CongressGovProvider')
    def test_ingestion_service_error_handling(self, mock_provider, mock_service, app, admin_token):
        """Test proper error handling when ingestion service fails."""
        mock_service_instance = MagicMock()
        mock_service_instance.run.side_effect = Exception("Database connection failed")
        mock_service.return_value = mock_service_instance

        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 500

    @patch('apps.api.app.routers.admin.IngestionService')
    @patch('apps.api.app.routers.admin.CongressGovProvider')
    def test_ingestion_zero_bills(self, mock_provider, mock_service, app, admin_token):
        """Test response when no bills are ingested."""
        mock_service_instance = MagicMock()
        mock_service_instance.run.return_value = 0
        mock_service.return_value = mock_service_instance

        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "Ingested 0 bills" in data["message"]

    @patch('apps.api.app.routers.admin.IngestionService')
    @patch('apps.api.app.routers.admin.CongressGovProvider')
    def test_ingestion_large_number_of_bills(self, mock_provider, mock_service, app, admin_token):
        """Test response with large number of ingested bills."""
        mock_service_instance = MagicMock()
        mock_service_instance.run.return_value = 9999
        mock_service.return_value = mock_service_instance

        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "9999" in data["message"]


class TestAdminAuthentication:
    """Test admin authentication security."""

    def test_case_sensitive_token(self, app, admin_token):
        """Test that admin token is case-sensitive."""
        client = TestClient(app)

        # Try with wrong case
        wrong_case_token = admin_token.upper()

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {wrong_case_token}"}
        )

        if wrong_case_token != admin_token:
            assert response.status_code == 403

    def test_token_with_extra_spaces(self, app, admin_token):
        """Test token with extra spaces is rejected."""
        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token} "}
        )

        assert response.status_code == 403

    def test_multiple_bearer_prefixes(self, app):
        """Test token with multiple Bearer prefixes is rejected."""
        client = TestClient(app)

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": "Bearer Bearer token"}
        )

        assert response.status_code == 403

    def test_partial_token_match(self, app, admin_token):
        """Test that partial token match is rejected."""
        client = TestClient(app)

        partial_token = admin_token[:20]  # Only first 20 characters

        response = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {partial_token}"}
        )

        assert response.status_code == 403


class TestAdminIntegration:
    """Integration tests for admin router."""

    @patch('apps.api.app.routers.admin.IngestionService')
    @patch('apps.api.app.routers.admin.CongressGovProvider')
    def test_multiple_ingestion_requests(self, mock_provider, mock_service, app, admin_token):
        """Test multiple sequential ingestion requests."""
        mock_service_instance = MagicMock()
        mock_service_instance.run.side_effect = [10, 15, 20]
        mock_service.return_value = mock_service_instance

        client = TestClient(app)

        # First request
        response1 = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response1.status_code == 200
        assert "10" in response1.json()["message"]

        # Second request
        response2 = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response2.status_code == 200
        assert "15" in response2.json()["message"]

        # Third request
        response3 = client.post(
            "/admin/ingest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response3.status_code == 200
        assert "20" in response3.json()["message"]

    def test_unauthorized_then_authorized_request(self, app, admin_token):
        """Test that unauthorized request followed by authorized request works."""
        client = TestClient(app)

        # First request with invalid token
        response1 = client.post(
            "/admin/ingest",
            headers={"Authorization": "Bearer invalid"}
        )
        assert response1.status_code == 403

        # Second request with valid token should work
        with patch('apps.api.app.routers.admin.IngestionService') as mock_service:
            with patch('apps.api.app.routers.admin.CongressGovProvider'):
                mock_service_instance = MagicMock()
                mock_service_instance.run.return_value = 5
                mock_service.return_value = mock_service_instance

                response2 = client.post(
                    "/admin/ingest",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert response2.status_code == 200
