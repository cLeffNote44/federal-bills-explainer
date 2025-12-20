"""Database utilities for FBX core."""

from .session import engine, SessionLocal

# Create aliases for backward compatibility
init_database = lambda *args, **kwargs: None  # No-op for now
get_database = lambda: engine
get_session = lambda: SessionLocal()

__all__ = ['engine', 'SessionLocal', 'init_database', 'get_database', 'get_session']
