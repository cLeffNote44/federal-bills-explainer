"""
Shared pytest fixtures and configuration for all tests.
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient
import os

# Set test environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an async database session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock = MagicMock()
    mock.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )
    return mock


@pytest.fixture
def mock_congress_api():
    """Mock Congress API responses."""
    mock = MagicMock()
    mock.get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "bills": [
                {
                    "bill_id": "hr1-118",
                    "title": "Test Bill",
                    "summary": "Test summary",
                    "introduced_date": "2024-01-01",
                }
            ]
        }
    )
    return mock


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from apps.api.app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Generate authentication headers for testing."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_bill_data():
    """Sample bill data for testing."""
    return {
        "bill_id": "hr1234-118",
        "title": "Sample Test Bill",
        "summary": "This is a test bill for unit testing",
        "introduced_date": "2024-01-15",
        "sponsor": "Test Sponsor",
        "committees": ["Committee on Testing"],
        "status": "introduced",
        "text": "Full text of the test bill...",
    }