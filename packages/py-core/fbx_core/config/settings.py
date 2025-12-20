"""
Environment-specific configuration management with validation.
"""
from pydantic import BaseSettings, Field, validator, EmailStr
from typing import List, Optional, Dict, Any
from enum import Enum
import os
import secrets


class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """
    Application settings with environment-specific configurations.
    
    Settings are loaded from environment variables and .env files.
    """
    
    # Application
    app_name: str = Field("Federal Bills Explainer", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    environment: Environment = Field(Environment.DEVELOPMENT, description="Current environment")
    debug: bool = Field(False, description="Debug mode")
    service_name: str = Field("federal-bills-api", description="Service identifier")
    
    # Security
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), description="Secret key for encryption")
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), description="JWT secret key")
    jwt_algorithm: str = Field("HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(30, description="Access token expiration in minutes")
    jwt_refresh_token_expire_days: int = Field(7, description="Refresh token expiration in days")
    allowed_hosts: List[str] = Field(["*"], description="Allowed hosts for the application")
    cors_origins: List[str] = Field(["http://localhost:3000"], description="CORS allowed origins")
    
    # Database
    database_url: str = Field(..., description="Database connection URL")
    database_pool_size: int = Field(20, description="Database connection pool size")
    database_max_overflow: int = Field(10, description="Maximum overflow connections")
    database_echo: bool = Field(False, description="Echo SQL statements")
    
    # Redis/Cache
    redis_url: Optional[str] = Field(None, description="Redis connection URL")
    cache_ttl: int = Field(300, description="Default cache TTL in seconds")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_model: str = Field("gpt-4", description="OpenAI model to use")
    openai_max_tokens: int = Field(2000, description="Maximum tokens for OpenAI responses")
    openai_temperature: float = Field(0.7, description="Temperature for OpenAI responses")
    
    # Congress API
    congress_api_key: Optional[str] = Field(None, description="Congress.gov API key")
    congress_api_base_url: str = Field("https://api.congress.gov/v3", description="Congress API base URL")
    congress_api_timeout: int = Field(30, description="Congress API timeout in seconds")
    
    # Rate Limiting
    rate_limit_anonymous: int = Field(100, description="Rate limit for anonymous users (requests/hour)")
    rate_limit_authenticated: int = Field(1000, description="Rate limit for authenticated users (requests/hour)")
    rate_limit_window_seconds: int = Field(3600, description="Rate limit window in seconds")
    
    # Logging
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field("json", description="Log format (json or text)")
    log_to_file: bool = Field(False, description="Whether to log to file")
    log_file_path: str = Field("/var/log/federal-bills/app.log", description="Log file path")
    log_pretty: bool = Field(False, description="Pretty print JSON logs")
    
    # Monitoring
    enable_metrics: bool = Field(True, description="Enable metrics collection")
    metrics_port: int = Field(9090, description="Metrics endpoint port")
    health_check_interval: int = Field(30, description="Health check interval in seconds")
    
    # Email (for notifications)
    smtp_host: Optional[str] = Field(None, description="SMTP server host")
    smtp_port: int = Field(587, description="SMTP server port")
    smtp_username: Optional[str] = Field(None, description="SMTP username")
    smtp_password: Optional[str] = Field(None, description="SMTP password")
    smtp_from_email: Optional[EmailStr] = Field(None, description="From email address")
    smtp_use_tls: bool = Field(True, description="Use TLS for SMTP")
    
    # Storage
    upload_max_size: int = Field(10 * 1024 * 1024, description="Maximum upload size in bytes")
    upload_allowed_extensions: List[str] = Field([".pdf", ".txt", ".docx"], description="Allowed file extensions")
    storage_backend: str = Field("local", description="Storage backend (local, s3)")
    storage_path: str = Field("/var/data/federal-bills", description="Local storage path")
    
    # AWS (if using S3)
    aws_access_key_id: Optional[str] = Field(None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(None, description="AWS secret access key")
    aws_region: str = Field("us-east-1", description="AWS region")
    s3_bucket: Optional[str] = Field(None, description="S3 bucket name")
    
    # Performance
    request_timeout: int = Field(60, description="Request timeout in seconds")
    worker_count: int = Field(4, description="Number of worker processes")
    thread_count: int = Field(2, description="Number of threads per worker")
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment setting."""
        if v == Environment.PRODUCTION:
            # In production, certain settings should be explicitly set
            if not os.getenv("JWT_SECRET_KEY"):
                raise ValueError("JWT_SECRET_KEY must be set in production")
            if not os.getenv("SECRET_KEY"):
                raise ValueError("SECRET_KEY must be set in production")
        return v
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_hosts", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from comma-separated string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v, values):
        """Validate database URL based on environment."""
        env = values.get("environment")
        if env == Environment.PRODUCTION and "sqlite" in v:
            raise ValueError("SQLite is not allowed in production")
        return v
    
    def get_redis_config(self) -> Optional[Dict[str, Any]]:
        """Get Redis configuration."""
        if not self.redis_url:
            return None
        
        # Parse Redis URL
        from urllib.parse import urlparse
        parsed = urlparse(self.redis_url)
        
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 6379,
            "password": parsed.password,
            "db": int(parsed.path[1:]) if parsed.path else 0,
        }
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == Environment.TESTING
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable prefix
        env_prefix = "FBX_"
        
        # Allow extra fields for forward compatibility
        extra = "allow"


# Create global settings instance
settings = Settings()