"""
FastAPI application entry point with security middleware and lifecycle management.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

# Core imports
from fbx_core.utils.settings import Settings
from fbx_core.config import startup_validation
from fbx_core.cache import init_cache, shutdown_cache
from fbx_core.middleware import (
    add_security_middleware,
    configure_cors,
    RateLimitMiddleware,
)

# Router imports
from app.routers import health, bills, admin, monitoring, export
from app.routers import auth, feedback, bookmarks, topics, tracking, comments

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Settings
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting Federal Bills Explainer API...")

    try:
        # Validate environment variables
        logger.info("Validating environment configuration...")
        startup_validation()
        logger.info("✓ Environment validation passed")

        # Initialize Redis cache
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            logger.info("Initializing Redis cache...")
            await init_cache(redis_url)
            logger.info("✓ Redis cache initialized")
        else:
            logger.warning("⚠ Redis URL not configured. Caching disabled.")

        # Additional startup tasks can go here
        logger.info("✓ Application startup complete")
        logger.info(f"📝 API Documentation: http://localhost:{os.getenv('API_PORT', '8000')}/docs")

    except Exception as e:
        logger.critical(f"✗ Startup failed: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down Federal Bills Explainer API...")

    try:
        # Close Redis cache
        await shutdown_cache()
        logger.info("✓ Redis cache closed")

        # Additional cleanup tasks can go here
        logger.info("✓ Application shutdown complete")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema with detailed documentation."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Federal Bills Explainer API",
        version="1.0.0",
        description="""## Federal Bills Explainer API

This API provides access to US federal bills data with AI-powered explanations.

### Features
- 📜 Browse and search federal bills
- 🤖 Get AI-generated explanations of complex legislation
- 📊 Track bill status and voting records
- 🔍 Advanced search and filtering capabilities
- 🔐 Secure authentication with JWT tokens
- 📈 Rate-limited public access
- 🚀 High-performance caching with Redis
- 🛡️ Comprehensive security headers

### Authentication
Some endpoints require authentication. Use the `/auth/login` endpoint to obtain a JWT token.
Include the token in the `Authorization` header as `Bearer <token>`.

### Rate Limiting
- Public endpoints: 100 requests per minute
- Search endpoints: 30 requests per minute
- Admin endpoints: 10 requests per minute
- Limits enforced per IP address
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### Response Formats
All responses are in JSON format with consistent error handling.

### Error Codes
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests (Rate Limited)
- `500`: Internal Server Error

### Security
- All sensitive endpoints require JWT authentication
- Passwords are hashed with bcrypt
- HTTPS enforced in production
- CORS configured for allowed origins only
- Rate limiting prevents abuse
- Security headers on all responses
        """,
        routes=app.routes,
        servers=[
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.federalbills.example.com", "description": "Production server"},
        ],
        tags=[
            {
                "name": "bills",
                "description": "Operations related to federal bills",
            },
            {
                "name": "auth",
                "description": "Authentication operations",
            },
            {
                "name": "admin",
                "description": "Admin operations (requires admin role)",
            },
            {
                "name": "health",
                "description": "Health check and monitoring",
            },
        ],
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Create FastAPI application
app = FastAPI(
    title="Federal Bills Explainer API",
    version="1.0.0",
    description="AI-powered platform for understanding US federal legislation",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Set custom OpenAPI schema
app.openapi = custom_openapi

# Configure CORS
cors_origins = [origin.strip() for origin in settings.cors_origins]
configure_cors(app, cors_origins)

# Add response compression (should be one of the first middleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# Add security middleware (order matters - added in reverse execution order)
max_request_size = int(os.getenv("MAX_REQUEST_SIZE", 10 * 1024 * 1024))
add_security_middleware(app, max_content_length=max_request_size)

# Add rate limiting middleware
redis_url = os.getenv("REDIS_URL")
app.add_middleware(RateLimitMiddleware, redis_url=redis_url)

# Include routers
app.include_router(health.router)
app.include_router(bills.router, prefix="/bills", tags=["bills"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(monitoring.router)
# New feature routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
app.include_router(bookmarks.router, prefix="/bookmarks", tags=["bookmarks"])
app.include_router(topics.router, prefix="/topics", tags=["topics"])
app.include_router(tracking.router, prefix="/tracking", tags=["tracking"])
app.include_router(comments.router, prefix="/comments", tags=["comments"])

# Initialize Prometheus instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/monitoring/metrics/prometheus", "/healthz"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Instrument app and expose metrics endpoint
instrumentator.instrument(app).expose(app, endpoint="/monitoring/metrics/prometheus", include_in_schema=False)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Federal Bills Explainer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/monitoring/health",
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
