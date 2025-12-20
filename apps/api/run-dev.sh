#!/bin/bash
# Development server script for Federal Bills Explainer API

# Set environment variables
export DATABASE_URL="postgresql+psycopg://fbx_user:iKHVS40dLQnXyeGZEmMDiwHX9yqN8zaB@localhost:5432/federal_bills"
export REDIS_URL="redis://localhost:6379/0"
export CONGRESS_API_KEY="BzGnbhAqV3hmHi6YiINH4SJGyDfjP5ZAfJBE3BIN"
export JWT_SECRET_KEY="18dde2e578f7d3fe84d1e36f30398ea63bcc41e45763ce4604a103b7b7c43cb7"
export ADMIN_TOKEN="630a6f83a72666b8197652bc86fe8df4364aab809d0f4e8709ae9ecc4aab7f42"
export CORS_ORIGINS="http://localhost:3000,http://localhost:3001"
export ENVIRONMENT="development"
export LOG_LEVEL="INFO"

# Activate virtual environment
source "$(dirname "$0")/venv/bin/activate"

# Run uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
