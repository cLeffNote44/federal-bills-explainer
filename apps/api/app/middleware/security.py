"""
Security middleware for the API.
"""
from fastapi import Request, HTTPException, status
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Dict, Optional
import time
import hashlib
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fbx_core.utils.logging import logger
import os


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS for production
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP header
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.congress.gov;"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with different limits for authenticated/unauthenticated users.
    """
    
    def __init__(self, app, default_limit: int = 100, window_seconds: int = 3600):
        super().__init__(app)
        self.default_limit = default_limit  # Requests per window
        self.window_seconds = window_seconds  # Time window in seconds
        self.request_history: Dict[str, deque] = defaultdict(deque)
        
        # Different limits based on user type
        self.limits = {
            "anonymous": 100,      # 100 requests per hour
            "authenticated": 1000, # 1000 requests per hour
            "admin": float('inf')  # Unlimited for admins
        }
    
    def get_client_id(self, request: Request) -> str:
        """Get a unique identifier for the client."""
        # Use IP address as identifier
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        # Add user ID if authenticated
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else None
        if user_id:
            return f"{ip}:{user_id}"
        return ip
    
    def get_rate_limit(self, request: Request) -> int:
        """Get rate limit based on user authentication status."""
        if hasattr(request.state, 'user_role'):
            if request.state.user_role == "admin":
                return self.limits["admin"]
            return self.limits["authenticated"]
        return self.limits["anonymous"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health") or request.url.path.startswith("/monitoring/health"):
            return await call_next(request)
        
        client_id = self.get_client_id(request)
        current_time = time.time()
        rate_limit = self.get_rate_limit(request)
        
        # Clean old requests from history
        history = self.request_history[client_id]
        cutoff_time = current_time - self.window_seconds
        while history and history[0] < cutoff_time:
            history.popleft()
        
        # Check rate limit
        if len(history) >= rate_limit and rate_limit != float('inf'):
            # Calculate retry after
            retry_after = int(history[0] + self.window_seconds - current_time)
            
            # Log rate limit violation
            logger.log_security_event(
                "rate_limit_exceeded",
                {
                    "client_id": client_id,
                    "requests_made": len(history),
                    "limit": rate_limit,
                    "retry_after": retry_after
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Add current request to history
        history.append(current_time)
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, rate_limit - len(history)))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests."""
    
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max request size
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            logger.log_security_event(
                "oversized_request",
                {
                    "path": request.url.path,
                    "content_length": content_length,
                    "max_allowed": self.MAX_CONTENT_LENGTH
                }
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too large. Maximum size is {self.MAX_CONTENT_LENGTH} bytes."
            )
        
        # Validate content type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data")):
                logger.log_security_event(
                    "invalid_content_type",
                    {
                        "path": request.url.path,
                        "method": request.method,
                        "content_type": content_type
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Unsupported media type. Use application/json or multipart/form-data."
                )
        
        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = hashlib.md5(
            f"{time.time()}{request.client.host if request.client else 'unknown'}".encode()
        ).hexdigest()[:12]
        
        # Store request ID in state
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        logger.set_request_context(request_id)
        logger.log_api_request(
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else "unknown"
        )
        
        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.log_api_response(
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.log_error(e, {"request_id": request_id, "duration_ms": duration_ms})
            raise
        finally:
            logger.clear_request_context()