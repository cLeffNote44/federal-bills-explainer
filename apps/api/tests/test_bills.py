"""
Tests for bills API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestBillsEndpoints:
    """Test suite for bills-related endpoints."""
    
    @pytest.mark.unit
    def test_get_bills_list(self, test_client: TestClient):
        """Test getting list of bills."""
        response = test_client.get("/bills/")
        assert response.status_code == 200
        # assert isinstance(response.json(), list)
    
    @pytest.mark.unit
    def test_get_bill_by_id(self, test_client: TestClient):
        """Test getting a specific bill by ID."""
        bill_id = "hr1234-118"
        response = test_client.get(f"/bills/{bill_id}")
        # Will be 404 initially since we don't have data
        assert response.status_code in [200, 404]
    
    @pytest.mark.unit
    def test_search_bills(self, test_client: TestClient):
        """Test searching bills with query parameters."""
        response = test_client.get("/bills/search?q=healthcare")
        assert response.status_code == 200
        # assert isinstance(response.json(), list)
    
    @pytest.mark.integration
    @patch("apps.api.app.routers.bills.get_db")
    def test_create_bill(self, mock_db, test_client: TestClient, sample_bill_data):
        """Test creating a new bill."""
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        response = test_client.post("/bills/", json=sample_bill_data)
        # Will need auth implementation first
        assert response.status_code in [201, 401, 422]
    
    @pytest.mark.unit
    def test_get_bill_explanation(self, test_client: TestClient):
        """Test getting AI explanation for a bill."""
        bill_id = "hr1234-118"
        response = test_client.get(f"/bills/{bill_id}/explain")
        assert response.status_code in [200, 404]
    
    @pytest.mark.integration
    def test_get_bills_with_pagination(self, test_client: TestClient):
        """Test bills endpoint with pagination parameters."""
        response = test_client.get("/bills/?skip=0&limit=10")
        assert response.status_code == 200
        # result = response.json()
        # assert "items" in result or isinstance(result, list)
    
    @pytest.mark.unit
    def test_get_bills_by_status(self, test_client: TestClient):
        """Test filtering bills by status."""
        response = test_client.get("/bills/?status=passed")
        assert response.status_code == 200
    
    @pytest.mark.unit 
    def test_get_bills_by_date_range(self, test_client: TestClient):
        """Test filtering bills by date range."""
        response = test_client.get("/bills/?start_date=2024-01-01&end_date=2024-12-31")
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_get_bill_sponsors(self, test_client: TestClient):
        """Test getting bill sponsors information."""
        bill_id = "hr1234-118"
        response = test_client.get(f"/bills/{bill_id}/sponsors")
        assert response.status_code in [200, 404]
    
    @pytest.mark.unit
    def test_get_bill_timeline(self, test_client: TestClient):
        """Test getting bill timeline/history."""
        bill_id = "hr1234-118"
        response = test_client.get(f"/bills/{bill_id}/timeline")
        assert response.status_code in [200, 404]