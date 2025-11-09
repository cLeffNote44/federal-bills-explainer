"""Settings and configuration for ingestion."""

from typing import Optional
from datetime import date
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Ingestion settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="INGEST_",
        case_sensitive=False,
    )
    
    # API Configuration
    congress_api_key: str = Field(..., description="Congress.gov API key")
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
        description="PostgreSQL connection URL"
    )
    
    # Model Configuration
    ingest_model_name: str = Field(
        default="google/flan-t5-base",
        description="Model for generating explanations"
    )
    embed_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Model for generating embeddings"
    )
    
    # Ingestion Configuration
    from_date: Optional[str] = Field(
        default=None,
        description="Start date for bill fetching (ISO format)"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date for bill fetching (ISO format)"
    )
    batch_size: int = Field(
        default=10,
        description="Number of bills to process in batch"
    )
    max_records: Optional[int] = Field(
        default=20,
        description="Maximum number of records to process"
    )
    dry_run: bool = Field(
        default=True,
        description="Run without persisting to database"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Performance
    use_gpu: bool = Field(
        default=False,
        description="Use GPU if available for models"
    )
    
    # Rate limiting
    api_delay_seconds: float = Field(
        default=0.5,
        description="Delay between API calls in seconds"
    )


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Get singleton settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
