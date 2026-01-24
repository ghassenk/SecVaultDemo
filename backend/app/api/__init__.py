"""API routes module."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.secrets import router as secrets_router

# Aggregate all routers
api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(secrets_router)

__all__ = ["api_router"]
