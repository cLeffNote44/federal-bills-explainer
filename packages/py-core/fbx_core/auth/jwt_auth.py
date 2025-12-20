"""
JWT authentication for Federal Bills Explainer API.

Provides token generation, validation, and authentication dependencies.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    scopes: list[str] = []
    exp: Optional[datetime] = None


class Token(BaseModel):
    """Access token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPair(BaseModel):
    """Access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_token_pair(username: str, scopes: list[str] = None) -> TokenPair:
    """
    Create access and refresh token pair.

    Args:
        username: Username to encode in tokens
        scopes: List of permission scopes

    Returns:
        TokenPair with access and refresh tokens
    """
    if scopes is None:
        scopes = ["read"]

    data = {"sub": username, "scopes": scopes}

    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def verify_token(token: str) -> TokenData:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData with decoded claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        scopes: list = payload.get("scopes", [])
        exp_timestamp: int = payload.get("exp")

        if username is None:
            raise credentials_exception

        exp = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None

        return TokenData(username=username, scopes=scopes, exp=exp)

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency to get current authenticated user.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    return verify_token(token)


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Dependency to get current active user.

    Can be extended to check user status in database.

    Args:
        current_user: Current user from token

    Returns:
        TokenData for active user
    """
    # TODO: Add database check for user status if needed
    return current_user


def require_scope(required_scope: str):
    """
    Dependency factory for scope-based authorization.

    Args:
        required_scope: Required permission scope

    Returns:
        Dependency function
    """
    async def scope_checker(
        current_user: TokenData = Depends(get_current_active_user)
    ) -> TokenData:
        if required_scope not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required scope: {required_scope}"
            )
        return current_user

    return scope_checker


# Admin authentication (simple token-based)
async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> bool:
    """
    Verify admin token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        True if valid admin token

    Raises:
        HTTPException: If token is invalid
    """
    admin_token = os.getenv("ADMIN_TOKEN", "")

    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin authentication not configured"
        )

    if credentials.credentials != admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


# Permission scopes
class Scopes:
    """Available permission scopes."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    INGEST = "ingest"
    EXPORT = "export"
