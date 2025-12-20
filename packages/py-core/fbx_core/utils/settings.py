from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, List, Union
from datetime import date

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/fbx"
    admin_token: str = "change-me"
    cors_origins: Union[List[str], str] = "http://localhost:3000"
    congress_api_key: Optional[str] = None
    jwt_secret_key: str = "change-me-in-production"

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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

