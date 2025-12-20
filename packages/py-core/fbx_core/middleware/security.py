"""
Security middleware for Federal Bills Explainer API.

Implements security headers, CORS, and request validation.
"""

from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Implements:
    - Content Security Policy (CSP)
    - X-Frame-Options
    - X-Content-Type-Options
    - Strict-Transport-Security (HSTS)
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        response = await call_next(request)

        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy
        permissions_policy = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)

        # HSTS (only in production with HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Remove server header to avoid leaking server info
        if "Server" in response.headers:
            del response.headers["Server"]

        # Add custom security header
        response.headers["X-Powered-By"] = "Federal Bills Explainer"

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request validation and size limiting.
    """

    def __init__(self, app, max_content_length: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_content_length = max_content_length

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": f"Request too large. Maximum size is {self.max_content_length} bytes"
                }
            )

        # Validate content type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
            ]
            if not any(ct in content_type for ct in allowed_types):
                logger.warning(f"Invalid content type: {content_type}")

        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all requests and responses.
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", f"req_{int(time.time() * 1000)}")

        # Log request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )

        start_time = time.time()

        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2),
                },
                exc_info=True
            )
            raise


def configure_cors(app, origins: list[str]) -> None:
    """
    Configure CORS middleware for the application.

    Args:
        app: FastAPI application instance
        origins: List of allowed origins
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Type",
            "Authorization",
            "X-Request-ID",
        ],
        expose_headers=["X-Request-ID"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    logger.info(f"CORS configured with origins: {origins}")


def add_security_middleware(app, max_content_length: int = 10 * 1024 * 1024) -> None:
    """
    Add all security middleware to the application.

    Args:
        app: FastAPI application instance
        max_content_length: Maximum allowed content length in bytes
    """
    # Add middlewares in reverse order (they execute in LIFO order)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestValidationMiddleware, max_content_length=max_content_length)
    app.add_middleware(RequestLoggingMiddleware)

    logger.info("Security middleware configured")
