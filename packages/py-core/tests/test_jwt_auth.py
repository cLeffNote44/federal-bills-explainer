"""
Tests for JWT authentication module.
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException

from fbx_core.auth import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    verify_token,
    TokenData,
    Scopes,
)


class TestTokenCreation:
    """Test token creation functions."""

    def test_create_access_token(self, monkeypatch):
        """Test access token creation."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        token = create_access_token(
            data={"sub": "testuser", "scopes": [Scopes.READ]}
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, monkeypatch):
        """Test refresh token creation."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        token = create_refresh_token(
            data={"sub": "testuser"}
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_pair(self, monkeypatch):
        """Test token pair creation."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        tokens = create_token_pair(
            username="testuser",
            scopes=[Scopes.READ, Scopes.WRITE]
        )

        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0

    def test_create_token_with_custom_expiry(self, monkeypatch):
        """Test token creation with custom expiration."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        expires_delta = timedelta(minutes=5)
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=expires_delta
        )

        assert isinstance(token, str)

        # Verify token
        token_data = verify_token(token)
        assert token_data.username == "testuser"

        # Check expiration is approximately 5 minutes from now
        exp_time = token_data.exp
        now = datetime.utcnow()
        time_diff = (exp_time - now).total_seconds()
        assert 290 < time_diff < 310  # Allow small variation


class TestTokenVerification:
    """Test token verification functions."""

    def test_verify_valid_token(self, monkeypatch):
        """Test verification of valid token."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        token = create_access_token(
            data={"sub": "testuser", "scopes": [Scopes.READ, Scopes.WRITE]}
        )

        token_data = verify_token(token)

        assert isinstance(token_data, TokenData)
        assert token_data.username == "testuser"
        assert Scopes.READ in token_data.scopes
        assert Scopes.WRITE in token_data.scopes
        assert isinstance(token_data.exp, datetime)

    def test_verify_token_without_subject(self, monkeypatch):
        """Test verification fails when token has no subject."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        token = create_access_token(data={})  # No 'sub' claim

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    def test_verify_expired_token(self, monkeypatch):
        """Test verification fails for expired token."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        # Create token that expires immediately
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-1)
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401

    def test_verify_invalid_token(self, monkeypatch):
        """Test verification fails for invalid token."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")

        assert exc_info.value.status_code == 401

    def test_verify_token_with_wrong_secret(self, monkeypatch):
        """Test verification fails when secret key changes."""
        monkeypatch.setenv("JWT_SECRET_KEY", "original-secret-key-32-characters")

        token = create_access_token(data={"sub": "testuser"})

        # Change secret key
        monkeypatch.setenv("JWT_SECRET_KEY", "different-secret-key-32-charactr")

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401


class TestScopes:
    """Test permission scopes."""

    def test_scopes_enum(self):
        """Test Scopes enum values."""
        assert Scopes.READ == "read"
        assert Scopes.WRITE == "write"
        assert Scopes.ADMIN == "admin"
        assert Scopes.INGEST == "ingest"
        assert Scopes.EXPORT == "export"

    def test_token_with_multiple_scopes(self, monkeypatch):
        """Test token with multiple permission scopes."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        all_scopes = [
            Scopes.READ,
            Scopes.WRITE,
            Scopes.ADMIN,
            Scopes.INGEST,
            Scopes.EXPORT
        ]

        token = create_access_token(
            data={"sub": "admin_user", "scopes": all_scopes}
        )

        token_data = verify_token(token)

        assert len(token_data.scopes) == 5
        for scope in all_scopes:
            assert scope in token_data.scopes

    def test_token_with_no_scopes(self, monkeypatch):
        """Test token with no scopes defaults to empty list."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        token = create_access_token(data={"sub": "testuser"})
        token_data = verify_token(token)

        assert token_data.scopes == []


class TestTokenData:
    """Test TokenData model."""

    def test_token_data_creation(self):
        """Test TokenData model creation."""
        exp = datetime.utcnow() + timedelta(hours=1)
        token_data = TokenData(
            username="testuser",
            scopes=[Scopes.READ],
            exp=exp
        )

        assert token_data.username == "testuser"
        assert token_data.scopes == [Scopes.READ]
        assert token_data.exp == exp

    def test_token_data_optional_fields(self):
        """Test TokenData with optional fields."""
        token_data = TokenData()

        assert token_data.username is None
        assert token_data.scopes == []
        assert token_data.exp is None


# Integration tests
class TestAuthenticationFlow:
    """Test complete authentication flows."""

    def test_complete_login_flow(self, monkeypatch):
        """Test complete login and token verification flow."""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32-characters-long")

        # Step 1: User logs in, receives tokens
        username = "john.doe@example.com"
        scopes = [Scopes.READ, Scopes.WRITE]

        tokens = create_token_pair(username=username, scopes=scopes)

        # Step 2: User makes request with access token
        token_data = verify_token(tokens.access_token)

        assert token_data.username == username
        assert set(token_data.scopes) == set(scopes)

        # Step 3: Access token expires, use refresh token
        refresh_data = verify_token(tokens.refresh_token)
        assert refresh_data.username == username

        # Step 4: Generate new access token using refresh token
        new_access_token = create_access_token(
            data={"sub": refresh_data.username, "scopes": refresh_data.scopes}
        )

        new_token_data = verify_token(new_access_token)
        assert new_token_data.username == username
