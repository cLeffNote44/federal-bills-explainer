from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fbx_core.utils.settings import Settings
from app.routers import health, bills, admin

settings = Settings()

# Custom OpenAPI schema
def custom_openapi():
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

### Authentication
Some endpoints require authentication. Use the `/auth/login` endpoint to obtain a JWT token.
Include the token in the `Authorization` header as `Bearer <token>`.

### Rate Limiting
- Anonymous users: 100 requests per hour
- Authenticated users: 1000 requests per hour
- Admin users: Unlimited

### Response Formats
All responses are in JSON format with consistent error handling.
        """,
        routes=app.routes,
        servers=[
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.federalbillsexplainer.com", "description": "Production server"}
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
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="Federal Bills Explainer API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(bills.router, prefix="/bills", tags=["bills"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
