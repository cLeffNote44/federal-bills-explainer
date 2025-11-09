"""Database connection and session management."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""
    
    def __init__(self, database_url: str):
        """Initialize database connection."""
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        
    def connect(self):
        """Create database engine and session factory."""
        # Use NullPool for better connection management with pgvector
        self.engine = create_engine(
            self.database_url,
            poolclass=NullPool,
            echo=False
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info("Database connection established")
        
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not connected. Call connect() first.")
            
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
            
    def disconnect(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# Global database instance
_db_instance: Database = None


def init_database(database_url: str) -> Database:
    """Initialize global database instance."""
    global _db_instance
    _db_instance = Database(database_url)
    _db_instance.connect()
    return _db_instance


def get_database() -> Database:
    """Get global database instance."""
    if not _db_instance:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_instance


def get_session() -> Generator[Session, None, None]:
    """Get database session from global instance."""
    db = get_database()
    yield from db.get_session()
