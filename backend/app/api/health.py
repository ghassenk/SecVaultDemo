"""
Health check endpoints.

These endpoints are used for:
- Container orchestration health probes
- Load balancer health checks
- Monitoring and alerting systems
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])

settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str
    environment: str


class DetailedHealthResponse(HealthResponse):
    """Detailed health check with component status."""

    database: str


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Returns application status. Use for simple liveness probes.",
)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get(
    "/ready",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Returns detailed status including database connectivity. Use for readiness probes.",
)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> DetailedHealthResponse:
    """
    Readiness check that verifies all dependencies.
    
    Checks:
    - Database connectivity
    """
    # Check database connection
    db_status = "unhealthy"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        pass

    return DetailedHealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        database=db_status,
    )
