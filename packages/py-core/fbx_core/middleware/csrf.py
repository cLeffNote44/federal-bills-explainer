"""
CSRF (Cross-Site Request Forgery) protection middleware.

Implements token-based CSRF protection for state-changing operations.
"""

import secrets
import hmac
import hashlib
import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class CSRFError(HTTPException):
    """CSRF validation error."""
    def __init__(self, detail: str = "CSRF validation failed"):
        super().__init__(status_code=403, detail=detail)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for CSRF protection on state-changing requests.

    Validates CSRF tokens for POST, PUT, PATCH, and DELETE requests.
    Tokens are validated using HMAC signatures with a secret key.
    """

    # HTTP methods that require CSRF protection
    PROTECTED_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

    # Endpoints that are exempt from CSRF protection
    EXEMPT_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/monitoring/health",
        "/monitoring/metrics",
        "/healthz",
    ]

    def __init__(
        self,
        app,
        secret_key: str,
        token_header: str = "X-CSRF-Token",
        cookie_name: str = "csrf_token",
        token_lifetime: int = 3600,  # 1 hour
    ):
        """
        Initialize CSRF protection middleware.

        Args:
            app: FastAPI application
            secret_key: Secret key for token generation
            token_header: Header name for CSRF token
            cookie_name: Cookie name for CSRF token
            token_lifetime: Token lifetime in seconds
        """
        super().__init__(app)
        self.secret_key = secret_key.encode()
        self.token_header = token_header
        self.cookie_name = cookie_name
        self.token_lifetime = token_lifetime

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and validate CSRF token if needed."""

        # Skip CSRF check for exempt paths
        if any(request.url.path.startswith(path) for path in self.EXEMPT_PATHS):
            return await call_next(request)

        # Skip CSRF check for safe methods (GET, HEAD, OPTIONS)
        if request.method not in self.PROTECTED_METHODS:
            response = await call_next(request)
            # Add CSRF token to safe responses
            self._set_csrf_token(response)
            return response

        # Validate CSRF token for state-changing methods
        try:
            self._validate_csrf_token(request)
            response = await call_next(request)
            return response
        except CSRFError as e:
            logger.warning(
                f"CSRF validation failed",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": request.client.host if request.client else None,
                }
            )
            return JSONResponse(
                status_code=403,
                content={"detail": str(e.detail)}
            )

    def _generate_token(self) -> str:
        """
        Generate a new CSRF token.

        Returns:
            CSRF token string
        """
        timestamp = str(int(time.time()))
        random_bytes = secrets.token_bytes(32)

        # Create message: timestamp + random_bytes
        message = f"{timestamp}:{random_bytes.hex()}".encode()

        # Create HMAC signature
        signature = hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).hexdigest()

        # Token format: timestamp:random:signature
        token = f"{timestamp}:{random_bytes.hex()}:{signature}"
        return token

    def _validate_csrf_token(self, request: Request) -> None:
        """
        Validate CSRF token from request.

        Args:
            request: FastAPI request object

        Raises:
            CSRFError: If token is missing or invalid
        """
        # Get token from header
        token_from_header = request.headers.get(self.token_header)

        # Get token from cookie
        token_from_cookie = request.cookies.get(self.cookie_name)

        # Check if token is present
        if not token_from_header:
            raise CSRFError(f"Missing CSRF token in {self.token_header} header")

        if not token_from_cookie:
            raise CSRFError(f"Missing CSRF token in {self.cookie_name} cookie")

        # Tokens must match
        if token_from_header != token_from_cookie:
            raise CSRFError("CSRF tokens do not match")

        # Validate token format
        try:
            timestamp_str, random_hex, signature = token_from_header.split(":")
            timestamp = int(timestamp_str)
        except (ValueError, AttributeError):
            raise CSRFError("Invalid CSRF token format")

        # Check token expiration
        current_time = int(time.time())
        if current_time - timestamp > self.token_lifetime:
            raise CSRFError("CSRF token has expired")

        # Verify HMAC signature
        message = f"{timestamp_str}:{random_hex}".encode()
        expected_signature = hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise CSRFError("Invalid CSRF token signature")

    def _set_csrf_token(self, response: Response) -> None:
        """
        Set CSRF token in response cookie.

        Args:
            response: FastAPI response object
        """
        # Generate new token
        token = self._generate_token()

        # Set cookie with secure flags
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=self.token_lifetime,
            httponly=True,
            secure=True,  # Only send over HTTPS
            samesite="strict",  # Prevent CSRF
        )

        # Also add to response header for easy access
        response.headers[self.token_header] = token


def generate_csrf_token(secret_key: str) -> str:
    """
    Generate a CSRF token (utility function).

    Args:
        secret_key: Secret key for token generation

    Returns:
        CSRF token string
    """
    timestamp = str(int(time.time()))
    random_bytes = secrets.token_bytes(32)
    message = f"{timestamp}:{random_bytes.hex()}".encode()

    signature = hmac.new(
        secret_key.encode(),
        message,
        hashlib.sha256
    ).hexdigest()

    return f"{timestamp}:{random_bytes.hex()}:{signature}"
