from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List
from datetime import date

class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/fbx"
    admin_token: str = "change-me"
    cors_origins: List[str] = ["http://localhost:3000"]
    congress_api_key: Optional[str] = None

    # Models
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    explain_model: str = "microsoft/phi-3-mini-4k-instruct"

    # Feature flags
    embeddings_enabled: bool = True
    explanations_enabled: bool = True

    # Ingestion controls
    ingest_limit: Optional[int] = None
    ingest_since: Optional[date] = None  # YYYY-MM-DD

    # Misc
    hf_home: Optional[str] = None
    dry_run: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from environment

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

