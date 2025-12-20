"""
Comprehensive tests for ingestion service.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fbx_core.models.tables import Base, Bill, Explanation, Embedding, IngestionState
from fbx_core.services.ingestion import IngestionService
from fbx_core.providers.base import BillRecord


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
def mock_provider():
    """Create mock provider."""
    provider = MagicMock()
    provider.name = "test_provider"
    return provider


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    with patch('fbx_core.services.ingestion.Settings') as mock:
        settings = Mock()
        settings.ingest_since = None
        settings.ingest_limit = None
        settings.explanations_enabled = False
        settings.embeddings_enabled = False
        settings.explain_model = "test-explain-model"
        settings.embedding_model = "test-embedding-model"
        mock.return_value = settings
        yield settings


class TestIngestionServiceInit:
    """Test IngestionService initialization."""

    def test_init_with_provider_and_session(self, mock_provider, test_db, mock_settings):
        """Test service initialization."""
        service = IngestionService(mock_provider, test_db)

        assert service.provider == mock_provider
        assert service.session == test_db
        assert service.settings == mock_settings


class TestIngestionServiceRun:
    """Test IngestionService.run() method."""

    def test_run_with_no_bills(self, mock_provider, test_db, mock_settings):
        """Test run with no bills to ingest."""
        mock_provider.fetch_bills_updated_since.return_value = iter([])

        service = IngestionService(mock_provider, test_db)
        count = service.run()

        assert count == 0
        mock_provider.fetch_bills_updated_since.assert_called_once()

    def test_run_with_single_bill(self, mock_provider, test_db, mock_settings):
        """Test run with single bill."""
        bill_data = {
            "congress": 118,
            "bill_type": "hr",
            "number": 1234,
            "title": "Test Bill",
            "summary": "Test summary",
            "status": "introduced",
        }
        mock_provider.fetch_bills_updated_since.return_value = iter([BillRecord(bill_data)])

        service = IngestionService(mock_provider, test_db)
        count = service.run()

        assert count == 1
        # Verify bill was created
        bills = test_db.query(Bill).all()
        assert len(bills) == 1
        assert bills[0].title == "Test Bill"

    def test_run_with_multiple_bills(self, mock_provider, test_db, mock_settings):
        """Test run with multiple bills."""
        bills_data = [
            {"congress": 118, "bill_type": "hr", "number": i, "title": f"Bill {i}"}
            for i in range(1, 6)
        ]
        mock_provider.fetch_bills_updated_since.return_value = iter([BillRecord(b) for b in bills_data])

        service = IngestionService(mock_provider, test_db)
        count = service.run()

        assert count == 5
        bills = test_db.query(Bill).all()
        assert len(bills) == 5

    def test_run_updates_ingestion_state(self, mock_provider, test_db, mock_settings):
        """Test that run updates ingestion state."""
        mock_provider.fetch_bills_updated_since.return_value = iter([])

        service = IngestionService(mock_provider, test_db)
        service.run()

        # Check ingestion state was created
        state = test_db.get(IngestionState, 1)
        assert state is not None
        assert state.last_run_at is not None

    def test_run_respects_ingest_limit(self, mock_provider, test_db, mock_settings):
        """Test that run respects ingest_limit setting."""
        mock_settings.ingest_limit = 3

        bills_data = [
            {"congress": 118, "bill_type": "hr", "number": i, "title": f"Bill {i}"}
            for i in range(1, 11)
        ]
        mock_provider.fetch_bills_updated_since.return_value = iter([BillRecord(b) for b in bills_data])

        service = IngestionService(mock_provider, test_db)
        count = service.run()

        assert count == 3
        bills = test_db.query(Bill).all()
        assert len(bills) == 3

    def test_run_with_ingest_since_override(self, mock_provider, test_db, mock_settings):
        """Test run with ingest_since setting override."""
        from datetime import date
        since_date = date(2024, 1, 1)
        mock_settings.ingest_since = since_date

        mock_provider.fetch_bills_updated_since.return_value = iter([])

        service = IngestionService(mock_provider, test_db)
        service.run()

        # Verify provider was called with correct since parameter
        call_args = mock_provider.fetch_bills_updated_since.call_args[0]
        assert call_args[0] is not None
        assert call_args[0].date() == since_date

    def test_run_uses_previous_state_timestamp(self, mock_provider, test_db, mock_settings):
        """Test run uses previous ingestion state timestamp."""
        # Create previous state
        previous_time = datetime.now(timezone.utc) - timedelta(days=1)
        state = IngestionState(id=1, last_run_at=previous_time)
        test_db.add(state)
        test_db.commit()

        mock_provider.fetch_bills_updated_since.return_value = iter([])

        service = IngestionService(mock_provider, test_db)
        service.run()

        # Verify provider was called with previous timestamp
        call_args = mock_provider.fetch_bills_updated_since.call_args[0]
        assert call_args[0] == previous_time


class TestIngestionServiceUpsertBill:
    """Test IngestionService._upsert_bill() method."""

    def test_upsert_creates_new_bill(self, mock_provider, test_db, mock_settings):
        """Test upserting creates new bill."""
        record = BillRecord({
            "congress": 118,
            "bill_type": "hr",
            "number": 1234,
            "title": "Test Bill",
            "summary": "Test summary",
            "status": "introduced",
        })

        service = IngestionService(mock_provider, test_db)
        bill = service._upsert_bill(record)

        assert bill is not None
        assert bill.congress == 118
        assert bill.bill_type == "hr"
        assert bill.number == 1234
        assert bill.title == "Test Bill"

    def test_upsert_updates_existing_bill(self, mock_provider, test_db, mock_settings):
        """Test upserting updates existing bill."""
        # Create existing bill
        existing = Bill(
            congress=118,
            bill_type="hr",
            number=1234,
            title="Old Title",
            summary="Old summary",
            status="introduced",
        )
        test_db.add(existing)
        test_db.commit()

        # Upsert with new data
        record = BillRecord({
            "congress": 118,
            "bill_type": "hr",
            "number": 1234,
            "title": "Updated Title",
            "summary": "Updated summary",
            "status": "passed",
        })

        service = IngestionService(mock_provider, test_db)
        bill = service._upsert_bill(record)

        assert bill is not None
        assert bill.title == "Updated Title"
        assert bill.summary == "Updated summary"
        assert bill.status == "passed"

        # Verify only one bill exists
        bills = test_db.query(Bill).all()
        assert len(bills) == 1

    def test_upsert_with_missing_required_fields(self, mock_provider, test_db, mock_settings):
        """Test upsert with missing required fields."""
        record = BillRecord({
            "title": "Test Bill",
            # Missing congress, bill_type, number
        })

        service = IngestionService(mock_provider, test_db)
        bill = service._upsert_bill(record)

        assert bill is None

    def test_upsert_with_all_optional_fields(self, mock_provider, test_db, mock_settings):
        """Test upsert with all optional fields."""
        from datetime import date
        record = BillRecord({
            "congress": 118,
            "bill_type": "hr",
            "number": 1234,
            "title": "Test Bill",
            "summary": "Test summary",
            "status": "enacted",
            "introduced_date": date(2024, 1, 1),
            "latest_action_date": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "congress_url": "https://congress.gov/bill/118/hr/1234",
            "public_law_number": "118-123",
            "sponsor": {"name": "Rep. Smith"},
            "committees": ["Committee on Energy"],
            "subjects": ["Energy", "Environment"],
            "cosponsors_count": 42,
        })

        service = IngestionService(mock_provider, test_db)
        bill = service._upsert_bill(record)

        assert bill is not None
        assert bill.public_law_number == "118-123"
        assert bill.cosponsors_count == 42
        assert bill.congress_url == "https://congress.gov/bill/118/hr/1234"

    def test_upsert_handles_database_error(self, mock_provider, test_db, mock_settings):
        """Test upsert handles database errors gracefully."""
        service = IngestionService(mock_provider, test_db)

        # Close session to simulate error
        test_db.close()

        record = BillRecord({
            "congress": 118,
            "bill_type": "hr",
            "number": 1234,
            "title": "Test Bill",
        })

        bill = service._upsert_bill(record)

        assert bill is None


class TestIngestionServiceGenerateExplanation:
    """Test IngestionService._generate_explanation() method."""

    @patch('fbx_core.services.ingestion.Settings')
    def test_generate_explanation_creates_explanation(self, mock_settings_class, mock_provider, test_db):
        """Test generating explanation for bill."""
        mock_settings = Mock()
        mock_settings.explanations_enabled = True
        mock_settings.explain_model = "test-model"
        mock_settings_class.return_value = mock_settings

        # Create bill
        bill = Bill(
            congress=118,
            bill_type="hr",
            number=1234,
            title="Healthcare Reform Act",
            summary="A bill to reform healthcare",
            status="introduced",
        )
        test_db.add(bill)
        test_db.commit()

        service = IngestionService(mock_provider, test_db)
        service._generate_explanation(bill)

        # Verify explanation was created
        explanations = test_db.query(Explanation).filter_by(bill_id=bill.id).all()
        assert len(explanations) == 1
        assert "Healthcare Reform Act" in explanations[0].text

    @patch('fbx_core.services.ingestion.Settings')
    def test_generate_explanation_skips_if_exists(self, mock_settings_class, mock_provider, test_db):
        """Test explanation generation skipped if already exists."""
        mock_settings = Mock()
        mock_settings.explanations_enabled = True
        mock_settings.explain_model = "test-model"
        mock_settings_class.return_value = mock_settings

        # Create bill with existing explanation
        bill = Bill(
            congress=118,
            bill_type="hr",
            number=1234,
            title="Test Bill",
            status="introduced",
        )
        test_db.add(bill)
        test_db.commit()

        explanation = Explanation(
            bill_id=bill.id,
            text="Existing explanation",
            model_name="test-model",
            version=1,
        )
        test_db.add(explanation)
        test_db.commit()

        service = IngestionService(mock_provider, test_db)
        service._generate_explanation(bill)

        # Should still have only one explanation
        explanations = test_db.query(Explanation).filter_by(bill_id=bill.id).all()
        assert len(explanations) == 1

    @patch('fbx_core.services.ingestion.Settings')
    def test_generate_explanation_handles_error(self, mock_settings_class, mock_provider, test_db):
        """Test explanation generation handles errors gracefully."""
        mock_settings = Mock()
        mock_settings.explanations_enabled = True
        mock_settings.explain_model = "test-model"
        mock_settings_class.return_value = mock_settings

        # Create bill without committing (will cause error)
        bill = Bill(
            congress=118,
            bill_type="hr",
            number=1234,
            title="Test Bill",
            status="introduced",
        )
        bill.id = 999  # Fake ID

        service = IngestionService(mock_provider, test_db)
        service._generate_explanation(bill)  # Should not raise exception


class TestIngestionServiceGenerateEmbedding:
    """Test IngestionService._generate_embedding() method."""

    @patch('fbx_core.services.ingestion.embed_text')
    @patch('fbx_core.services.ingestion.compute_text_and_hash')
    @patch('fbx_core.services.ingestion.Settings')
    def test_generate_embedding_creates_embedding(
        self, mock_settings_class, mock_compute, mock_embed, mock_provider, test_db
    ):
        """Test generating embedding for bill."""
        mock_settings = Mock()
        mock_settings.embeddings_enabled = True
        mock_settings.embedding_model = "test-model"
        mock_settings_class.return_value = mock_settings

        mock_compute.return_value = ("combined text", "hash123")
        mock_embed.return_value = [0.1] * 384

        # Create bill
        bill = Bill(
            congress=118,
            bill_type="hr",
            number=1234,
            title="Test Bill",
            summary="Test summary",
            status="introduced",
        )
        test_db.add(bill)
        test_db.commit()

        service = IngestionService(mock_provider, test_db)
        service._generate_embedding(bill)

        # Verify embedding was created
        embeddings = test_db.query(Embedding).filter_by(bill_id=bill.id).all()
        assert len(embeddings) == 1
        assert embeddings[0].content_hash == "hash123"
        assert len(embeddings[0].vector) == 384

    @patch('fbx_core.services.ingestion.embed_text')
    @patch('fbx_core.services.ingestion.compute_text_and_hash')
    @patch('fbx_core.services.ingestion.Settings')
    def test_generate_embedding_skips_if_exists(
        self, mock_settings_class, mock_compute, mock_embed, mock_provider, test_db
    ):
        """Test embedding generation skipped if already exists."""
        mock_settings = Mock()
        mock_settings.embeddings_enabled = True
        mock_settings.embedding_model = "test-model"
        mock_settings_class.return_value = mock_settings

        content_hash = "existing-hash"
        mock_compute.return_value = ("combined text", content_hash)

        # Create bill with existing embedding
        bill = Bill(
            congress=118,
            bill_type="hr",
            number=1234,
            title="Test Bill",
            status="introduced",
        )
        test_db.add(bill)
        test_db.commit()

        embedding = Embedding(
            bill_id=bill.id,
            content_kind="document",
            model_name="test-model",
            content_hash=content_hash,
            vector=[0.1] * 384,
        )
        test_db.add(embedding)
        test_db.commit()

        service = IngestionService(mock_provider, test_db)
        service._generate_embedding(bill)

        # Should still have only one embedding
        embeddings = test_db.query(Embedding).filter_by(bill_id=bill.id).all()
        assert len(embeddings) == 1

        # embed_text should not have been called
        mock_embed.assert_not_called()

    @patch('fbx_core.services.ingestion.embed_text')
    @patch('fbx_core.services.ingestion.compute_text_and_hash')
    @patch('fbx_core.services.ingestion.Settings')
    def test_generate_embedding_includes_explanation(
        self, mock_settings_class, mock_compute, mock_embed, mock_provider, test_db
    ):
        """Test embedding generation includes explanation text."""
        mock_settings = Mock()
        mock_settings.embeddings_enabled = True
        mock_settings.embedding_model = "test-model"
        mock_settings_class.return_value = mock_settings

        mock_compute.return_value = ("combined text", "hash123")
        mock_embed.return_value = [0.1] * 384

        # Create bill with explanation
        bill = Bill(
            congress=118,
            bill_type="hr",
            number=1234,
            title="Test Bill",
            summary="Test summary",
            status="introduced",
        )
        test_db.add(bill)
        test_db.commit()

        explanation = Explanation(
            bill_id=bill.id,
            text="This is an explanation",
            model_name="test-model",
            version=1,
        )
        test_db.add(explanation)
        test_db.commit()

        service = IngestionService(mock_provider, test_db)
        service._generate_embedding(bill)

        # Verify compute_text_and_hash was called with explanation
        mock_compute.assert_called_once()
        args = mock_compute.call_args[0]
        assert args[2] == "This is an explanation"  # Third arg is explanation text


class TestIngestionIntegration:
    """Integration tests for ingestion service."""

    @patch('fbx_core.services.ingestion.embed_text')
    @patch('fbx_core.services.ingestion.compute_text_and_hash')
    def test_full_ingestion_workflow(self, mock_compute, mock_embed, mock_provider, test_db, mock_settings):
        """Test complete ingestion workflow."""
        mock_settings.explanations_enabled = True
        mock_settings.embeddings_enabled = True

        mock_compute.return_value = ("combined text", "hash123")
        mock_embed.return_value = [0.1] * 384

        # Mock provider with test data
        bills_data = [
            {
                "congress": 118,
                "bill_type": "hr",
                "number": i,
                "title": f"Bill {i}",
                "summary": f"Summary {i}",
                "status": "introduced",
            }
            for i in range(1, 4)
        ]
        mock_provider.fetch_bills_updated_since.return_value = iter([BillRecord(b) for b in bills_data])

        service = IngestionService(mock_provider, test_db)
        count = service.run()

        assert count == 3

        # Verify bills were created
        bills = test_db.query(Bill).all()
        assert len(bills) == 3

        # Verify explanations were created
        explanations = test_db.query(Explanation).all()
        assert len(explanations) == 3

        # Verify embeddings were created
        embeddings = test_db.query(Embedding).all()
        assert len(embeddings) == 3

        # Verify state was updated
        state = test_db.get(IngestionState, 1)
        assert state is not None
        assert state.last_run_at is not None
