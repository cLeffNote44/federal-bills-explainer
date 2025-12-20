"""
Comprehensive tests for bills router.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

from fbx_core.models.tables import Base, Bill, Explanation, Embedding
from apps.api.app.routers import bills


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
def sample_bills(test_db):
    """Create sample bills for testing."""
    bills_data = [
        Bill(
            congress=118,
            bill_type="hr",
            number=1234,
            title="Healthcare Reform Act",
            summary="A bill to reform healthcare",
            status="introduced",
            public_law_number=None,
        ),
        Bill(
            congress=118,
            bill_type="s",
            number=5678,
            title="Education Funding Bill",
            summary="Increase education funding",
            status="passed",
            public_law_number="118-45",
        ),
        Bill(
            congress=117,
            bill_type="hr",
            number=9999,
            title="Infrastructure Investment Act",
            summary="Invest in infrastructure",
            status="enacted",
            public_law_number="117-123",
        ),
    ]

    for bill in bills_data:
        test_db.add(bill)
    test_db.commit()

    # Add explanation to first bill
    explanation = Explanation(
        bill_id=bills_data[0].id,
        text="This bill aims to reform the healthcare system by...",
        model_name="test-model",
    )
    test_db.add(explanation)
    test_db.commit()

    return bills_data


class TestListBills:
    """Test GET /bills endpoint."""

    def test_list_bills_no_filters(self, test_db, sample_bills):
        """Test listing all bills without filters."""
        # Override dependency
        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        response = client.get("/bills")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("congress" in bill for bill in data)
        assert all("title" in bill for bill in data)

    def test_list_bills_with_query(self, test_db, sample_bills):
        """Test searching bills by query."""
        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        response = client.get("/bills?q=healthcare")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Healthcare" in data[0]["title"]

    def test_list_bills_with_status_filter(self, test_db, sample_bills):
        """Test filtering bills by status."""
        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        response = client.get("/bills?status=passed")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["public_law_number"] == "118-45"

    def test_list_bills_pagination(self, test_db, sample_bills):
        """Test bill list pagination."""
        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        # Page 1 with page_size=2
        response = client.get("/bills?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Page 2 with page_size=2
        response = client.get("/bills?page=2&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_bills_invalid_page(self, test_db, sample_bills):
        """Test invalid page parameter."""
        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        response = client.get("/bills?page=0")
        assert response.status_code == 422  # Validation error


class TestGetBill:
    """Test GET /bills/{congress}/{bill_type}/{number} endpoint."""

    def test_get_bill_success(self, test_db, sample_bills):
        """Test retrieving a specific bill."""
        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        response = client.get("/bills/118/hr/1234")

        assert response.status_code == 200
        data = response.json()
        assert data["bill"]["congress"] == 118
        assert data["bill"]["bill_type"] == "hr"
        assert data["bill"]["number"] == 1234
        assert "Healthcare" in data["bill"]["title"]
        assert data["explanation"] is not None

    def test_get_bill_not_found(self, test_db, sample_bills):
        """Test retrieving non-existent bill."""
        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        response = client.get("/bills/999/hr/9999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_bill_no_explanation(self, test_db, sample_bills):
        """Test bill without explanation."""
        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        response = client.get("/bills/118/s/5678")

        assert response.status_code == 200
        data = response.json()
        assert data["bill"]["title"] == "Education Funding Bill"
        assert data["explanation"] is None


class TestSemanticSearch:
    """Test GET /bills/search endpoint."""

    @patch('apps.api.app.routers.bills.embed_text')
    def test_semantic_search(self, mock_embed, test_db, sample_bills):
        """Test semantic search functionality."""
        # Mock embedding function
        mock_embed.return_value = [0.1] * 384  # Mock 384-dim vector

        # Add embeddings to bills
        for bill in sample_bills:
            embedding = Embedding(
                bill_id=bill.id,
                vector=[0.1] * 384,
                model_name="test-model",
                content_kind="summary",
            )
            test_db.add(embedding)
        test_db.commit()

        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        response = client.get("/bills/search?q=healthcare")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all("congress" in bill for bill in data)
        mock_embed.assert_called_once()

    @patch('apps.api.app.routers.bills.embed_text')
    def test_semantic_search_pagination(self, mock_embed, test_db, sample_bills):
        """Test semantic search with pagination."""
        mock_embed.return_value = [0.1] * 384

        # Add embeddings
        for bill in sample_bills:
            embedding = Embedding(
                bill_id=bill.id,
                vector=[0.1] * 384,
                model_name="test-model",
                content_kind="summary",
            )
            test_db.add(embedding)
        test_db.commit()

        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        response = client.get("/bills/search?q=test&page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_semantic_search_missing_query(self, test_db):
        """Test semantic search without query parameter."""
        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        response = client.get("/bills/search")

        assert response.status_code == 422  # Validation error - q is required


class TestBillsIntegration:
    """Integration tests for bills router."""

    def test_full_workflow(self, test_db, sample_bills):
        """Test complete workflow: list, search, get details."""
        def override_get_db():
            yield test_db

        bills.get_db = override_get_db

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(bills.router, prefix="/bills")
        client = TestClient(app)

        # 1. List all bills
        response = client.get("/bills")
        assert response.status_code == 200
        all_bills = response.json()
        assert len(all_bills) == 3

        # 2. Search for specific bill
        response = client.get("/bills?q=healthcare")
        assert response.status_code == 200
        search_results = response.json()
        assert len(search_results) == 1

        # 3. Get bill details
        bill = search_results[0]
        response = client.get(f"/bills/{bill['congress']}/{bill['bill_type']}/{bill['number']}")
        assert response.status_code == 200
        details = response.json()
        assert details["bill"]["title"] == bill["title"]
        assert details["explanation"] is not None
