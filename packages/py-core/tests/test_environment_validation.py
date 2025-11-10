"""
Tests for environment validation module.
"""

import os
import pytest
from fbx_core.config import (
    EnvironmentValidator,
    ConfigError,
    validate_environment,
)


class TestEnvironmentValidator:
    """Test suite for EnvironmentValidator class."""

    def test_validate_all_with_missing_required_vars(self, monkeypatch):
        """Test that missing required variables raise ConfigError in strict mode."""
        # Clear all required variables
        for var in EnvironmentValidator.REQUIRED_VARS:
            monkeypatch.delenv(var, raising=False)

        with pytest.raises(ConfigError) as exc_info:
            EnvironmentValidator.validate_all(strict=True)

        error_message = str(exc_info.value)
        assert "Required environment variable" in error_message
        assert "DATABASE_URL" in error_message

    def test_validate_all_with_weak_passwords(self, monkeypatch):
        """Test weak password detection."""
        # Set required vars with weak values
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("CONGRESS_API_KEY", "test-key-12345678901234567890")
        monkeypatch.setenv("JWT_SECRET_KEY", "change-me")
        monkeypatch.setenv("ADMIN_TOKEN", "admin")

        # Should not raise in non-strict mode, but should log warnings
        config = EnvironmentValidator.validate_all(strict=False)

        assert config["JWT_SECRET_KEY"] == "change-me"
        assert config["ADMIN_TOKEN"] == "admin"

    def test_validate_all_with_valid_config(self, monkeypatch):
        """Test successful validation with valid configuration."""
        # Set all required variables with strong values
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("CONGRESS_API_KEY", "a" * 32)
        monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ADMIN_TOKEN", "b" * 32)

        config = EnvironmentValidator.validate_all(strict=True)

        assert config["DATABASE_URL"] == "postgresql://user:pass@localhost/db"
        assert len(config["JWT_SECRET_KEY"]) == 32
        assert len(config["ADMIN_TOKEN"]) == 32

    def test_is_weak_value_detection(self):
        """Test weak value detection logic."""
        # Test weak values
        assert EnvironmentValidator._is_weak_value("JWT_SECRET_KEY", "change-me")
        assert EnvironmentValidator._is_weak_value("JWT_SECRET_KEY", "password")
        assert EnvironmentValidator._is_weak_value("JWT_SECRET_KEY", "secret")
        assert EnvironmentValidator._is_weak_value("ADMIN_TOKEN", "admin")
        assert EnvironmentValidator._is_weak_value("JWT_SECRET_KEY", "short")

        # Test strong values
        assert not EnvironmentValidator._is_weak_value("JWT_SECRET_KEY", "a" * 32)
        assert not EnvironmentValidator._is_weak_value(
            "ADMIN_TOKEN",
            "super-strong-random-token-value-12345"
        )

    def test_validate_database_url(self, monkeypatch):
        """Test DATABASE_URL validation."""
        # Invalid database URL
        for var in EnvironmentValidator.REQUIRED_VARS:
            if var != "DATABASE_URL":
                monkeypatch.setenv(var, "x" * 32)

        monkeypatch.setenv("DATABASE_URL", "mysql://localhost/db")

        with pytest.raises(ConfigError) as exc_info:
            EnvironmentValidator.validate_all(strict=True)

        assert "DATABASE_URL must start with 'postgresql://'" in str(exc_info.value)

    def test_validate_redis_url(self, monkeypatch):
        """Test REDIS_URL validation."""
        # Set required vars
        for var in EnvironmentValidator.REQUIRED_VARS:
            monkeypatch.setenv(var, "x" * 32 if "KEY" in var or "TOKEN" in var else "postgresql://localhost/db")

        # Invalid Redis URL
        monkeypatch.setenv("REDIS_URL", "http://localhost:6379")

        with pytest.raises(ConfigError) as exc_info:
            EnvironmentValidator.validate_all(strict=True)

        assert "REDIS_URL must start with 'redis://'" in str(exc_info.value)

    def test_validate_log_level(self, monkeypatch):
        """Test LOG_LEVEL validation."""
        for var in EnvironmentValidator.REQUIRED_VARS:
            monkeypatch.setenv(var, "x" * 32 if "KEY" in var or "TOKEN" in var else "postgresql://localhost/db")

        monkeypatch.setenv("LOG_LEVEL", "INVALID")

        with pytest.raises(ConfigError) as exc_info:
            EnvironmentValidator.validate_all(strict=True)

        assert "LOG_LEVEL must be one of" in str(exc_info.value)

    def test_get_bool(self, monkeypatch):
        """Test boolean environment variable parsing."""
        # True values
        for true_val in ["true", "True", "TRUE", "1", "yes", "YES", "on"]:
            monkeypatch.setenv("TEST_BOOL", true_val)
            assert EnvironmentValidator.get_bool("TEST_BOOL") is True

        # False values
        for false_val in ["false", "False", "FALSE", "0", "no", "NO", "off"]:
            monkeypatch.setenv("TEST_BOOL", false_val)
            assert EnvironmentValidator.get_bool("TEST_BOOL") is False

        # Default
        monkeypatch.delenv("TEST_BOOL", raising=False)
        assert EnvironmentValidator.get_bool("TEST_BOOL", default=True) is True
        assert EnvironmentValidator.get_bool("TEST_BOOL", default=False) is False

    def test_get_int(self, monkeypatch):
        """Test integer environment variable parsing."""
        monkeypatch.setenv("TEST_INT", "42")
        assert EnvironmentValidator.get_int("TEST_INT") == 42

        monkeypatch.setenv("TEST_INT", "invalid")
        assert EnvironmentValidator.get_int("TEST_INT", default=100) == 100

        monkeypatch.delenv("TEST_INT", raising=False)
        assert EnvironmentValidator.get_int("TEST_INT", default=50) == 50

    def test_get_list(self, monkeypatch):
        """Test list environment variable parsing."""
        monkeypatch.setenv("TEST_LIST", "item1,item2,item3")
        assert EnvironmentValidator.get_list("TEST_LIST") == ["item1", "item2", "item3"]

        monkeypatch.setenv("TEST_LIST", "item1, item2 , item3")
        assert EnvironmentValidator.get_list("TEST_LIST") == ["item1", "item2", "item3"]

        monkeypatch.setenv("TEST_LIST", "")
        assert EnvironmentValidator.get_list("TEST_LIST", default=["default"]) == ["default"]

        monkeypatch.delenv("TEST_LIST", raising=False)
        assert EnvironmentValidator.get_list("TEST_LIST") == []

    def test_validate_boolean_vars(self, monkeypatch):
        """Test validation of boolean environment variables."""
        for var in EnvironmentValidator.REQUIRED_VARS:
            monkeypatch.setenv(var, "x" * 32 if "KEY" in var or "TOKEN" in var else "postgresql://localhost/db")

        monkeypatch.setenv("DRY_RUN", "invalid")

        with pytest.raises(ConfigError) as exc_info:
            EnvironmentValidator.validate_all(strict=True)

        assert "must be a boolean value" in str(exc_info.value)

    def test_validate_numeric_vars(self, monkeypatch):
        """Test validation of numeric environment variables."""
        for var in EnvironmentValidator.REQUIRED_VARS:
            monkeypatch.setenv(var, "x" * 32 if "KEY" in var or "TOKEN" in var else "postgresql://localhost/db")

        # Invalid MAX_REQUEST_SIZE
        monkeypatch.setenv("MAX_REQUEST_SIZE", "invalid")

        with pytest.raises(ConfigError) as exc_info:
            EnvironmentValidator.validate_all(strict=True)

        assert "MAX_REQUEST_SIZE must be a valid integer" in str(exc_info.value)

        # Zero value
        monkeypatch.setenv("MAX_REQUEST_SIZE", "0")

        with pytest.raises(ConfigError) as exc_info:
            EnvironmentValidator.validate_all(strict=True)

        assert "MAX_REQUEST_SIZE must be a positive integer" in str(exc_info.value)


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_validate_environment(self, monkeypatch):
        """Test validate_environment convenience function."""
        for var in EnvironmentValidator.REQUIRED_VARS:
            monkeypatch.setenv(var, "x" * 32 if "KEY" in var or "TOKEN" in var else "postgresql://localhost/db")

        config = validate_environment(strict=True)
        assert isinstance(config, dict)
        assert "DATABASE_URL" in config
