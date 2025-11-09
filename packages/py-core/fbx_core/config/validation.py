"""
Environment variable validation and configuration.

Ensures all required environment variables are set with proper values.
"""

import os
import sys
import logging
from typing import Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass


class EnvironmentValidator:
    """
    Validates environment variables and configuration.
    """

    REQUIRED_VARS = [
        "DATABASE_URL",
        "CONGRESS_API_KEY",
        "JWT_SECRET_KEY",
        "ADMIN_TOKEN",
    ]

    OPTIONAL_VARS = {
        "REDIS_URL": "redis://localhost:6379/0",
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "INFO",
        "CORS_ORIGINS": "http://localhost:3000",
        "DRY_RUN": "false",
        "EMBEDDINGS_ENABLED": "false",
        "EXPLANATIONS_ENABLED": "false",
        "MAX_REQUEST_SIZE": "10485760",  # 10MB
        "SESSION_TIMEOUT": "3600",
        "FORCE_HTTPS": "false",
    }

    @classmethod
    def validate_all(cls, strict: bool = True) -> dict[str, Any]:
        """
        Validate all environment variables.

        Args:
            strict: If True, raises ConfigError for missing required vars.
                   If False, logs warnings only.

        Returns:
            Dictionary of validated configuration values.

        Raises:
            ConfigError: If required variables are missing or invalid (strict mode).
        """
        config = {}
        errors = []
        warnings = []

        # Check required variables
        for var in cls.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                errors.append(f"Required environment variable '{var}' is not set")
            elif cls._is_weak_value(var, value):
                warnings.append(
                    f"Environment variable '{var}' has a weak/default value: {value}"
                )
            config[var] = value

        # Set optional variables with defaults
        for var, default in cls.OPTIONAL_VARS.items():
            config[var] = os.getenv(var, default)

        # Validate specific values
        validation_errors = cls._validate_values(config)
        errors.extend(validation_errors)

        # Handle errors
        if errors:
            error_msg = "\n".join(errors)
            logger.error(f"Configuration errors:\n{error_msg}")
            if strict:
                raise ConfigError(f"Configuration validation failed:\n{error_msg}")

        # Handle warnings
        if warnings:
            warning_msg = "\n".join(warnings)
            logger.warning(f"Configuration warnings:\n{warning_msg}")

        logger.info("Environment validation completed successfully")
        return config

    @staticmethod
    def _is_weak_value(var: str, value: str) -> bool:
        """Check if value is weak or default."""
        weak_values = [
            "change-me",
            "change_me",
            "changeme",
            "password",
            "secret",
            "admin",
            "test",
        ]

        # Check for weak values
        value_lower = value.lower()
        if any(weak in value_lower for weak in weak_values):
            return True

        # Check for short secrets
        if var in ["JWT_SECRET_KEY", "ADMIN_TOKEN"]:
            if len(value) < 32:
                return True

        return False

    @staticmethod
    def _validate_values(config: dict[str, Any]) -> list[str]:
        """Validate specific configuration values."""
        errors = []

        # Validate DATABASE_URL
        db_url = config.get("DATABASE_URL", "")
        if db_url and not db_url.startswith("postgresql"):
            errors.append("DATABASE_URL must start with 'postgresql://'")

        # Validate REDIS_URL
        redis_url = config.get("REDIS_URL", "")
        if redis_url and not redis_url.startswith("redis://"):
            errors.append("REDIS_URL must start with 'redis://'")

        # Validate LOG_LEVEL
        log_level = config.get("LOG_LEVEL", "INFO")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() not in valid_levels:
            errors.append(
                f"LOG_LEVEL must be one of {valid_levels}, got '{log_level}'"
            )

        # Validate ENVIRONMENT
        env = config.get("ENVIRONMENT", "development")
        valid_envs = ["development", "staging", "production"]
        if env not in valid_envs:
            errors.append(
                f"ENVIRONMENT must be one of {valid_envs}, got '{env}'"
            )

        # Validate boolean values
        bool_vars = ["DRY_RUN", "EMBEDDINGS_ENABLED", "EXPLANATIONS_ENABLED", "FORCE_HTTPS"]
        for var in bool_vars:
            value = config.get(var, "").lower()
            if value and value not in ["true", "false", "1", "0", "yes", "no"]:
                errors.append(
                    f"{var} must be a boolean value (true/false), got '{value}'"
                )

        # Validate numeric values
        try:
            max_size = int(config.get("MAX_REQUEST_SIZE", "0"))
            if max_size <= 0:
                errors.append("MAX_REQUEST_SIZE must be a positive integer")
        except ValueError:
            errors.append("MAX_REQUEST_SIZE must be a valid integer")

        try:
            timeout = int(config.get("SESSION_TIMEOUT", "0"))
            if timeout <= 0:
                errors.append("SESSION_TIMEOUT must be a positive integer")
        except ValueError:
            errors.append("SESSION_TIMEOUT must be a valid integer")

        return errors

    @staticmethod
    def get_bool(var: str, default: bool = False) -> bool:
        """Get environment variable as boolean."""
        value = os.getenv(var, str(default)).lower()
        return value in ["true", "1", "yes", "on"]

    @staticmethod
    def get_int(var: str, default: int = 0) -> int:
        """Get environment variable as integer."""
        try:
            return int(os.getenv(var, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer value for {var}, using default: {default}")
            return default

    @staticmethod
    def get_list(var: str, default: Optional[list] = None, separator: str = ",") -> list:
        """Get environment variable as list."""
        if default is None:
            default = []
        value = os.getenv(var, "")
        if not value:
            return default
        return [item.strip() for item in value.split(separator) if item.strip()]

    @staticmethod
    def print_config_summary(config: dict[str, Any], mask_secrets: bool = True) -> None:
        """
        Print configuration summary.

        Args:
            config: Configuration dictionary
            mask_secrets: If True, masks secret values
        """
        secret_vars = ["PASSWORD", "SECRET", "KEY", "TOKEN"]

        print("\n" + "="*60)
        print("CONFIGURATION SUMMARY")
        print("="*60)

        for key, value in sorted(config.items()):
            if mask_secrets and any(secret in key.upper() for secret in secret_vars):
                if value:
                    masked = value[:4] + "*" * (len(value) - 8) + value[-4:]
                    print(f"{key:30} = {masked}")
                else:
                    print(f"{key:30} = (not set)")
            else:
                print(f"{key:30} = {value}")

        print("="*60 + "\n")


def validate_environment(strict: bool = True) -> dict[str, Any]:
    """
    Convenience function to validate environment.

    Args:
        strict: If True, raises ConfigError for invalid config.

    Returns:
        Validated configuration dictionary.
    """
    return EnvironmentValidator.validate_all(strict=strict)


def startup_validation() -> None:
    """
    Run validation on application startup.

    This should be called early in the application initialization.
    """
    try:
        config = validate_environment(strict=True)
        EnvironmentValidator.print_config_summary(config)
        logger.info("✓ Environment validation passed")
    except ConfigError as e:
        logger.critical(f"✗ Environment validation failed: {e}")
        logger.critical("Please check your .env file and ensure all required variables are set.")
        logger.critical("See .env.example for reference.")
        sys.exit(1)
