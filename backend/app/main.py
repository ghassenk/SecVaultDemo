"""
SecureVault - Main Application Entry Point

A security-focused personal secrets manager demonstrating
application security best practices.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api import api_router
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.security import (
    configure_cors,
    configure_rate_limiting,
    configure_security_headers,
    limiter,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Startup:
    - Initialize database connection
    - Run any startup tasks
    
    Shutdown:
    - Close database connections
    - Cleanup resources
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Only initialize DB if not in test mode (tests handle their own DB)
    if settings.environment != "testing":
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    if settings.environment != "testing":
        await close_db()
        logger.info("Database connections closed")


def create_application() -> FastAPI:
    """
    Application factory.
    
    Creates and configures the FastAPI application with:
    - Security middleware
    - CORS configuration
    - Rate limiting
    - API routers
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A security-focused personal secrets manager",
        docs_url="/docs" if settings.debug else None,  # Disable docs in production
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # Configure security (order matters - CORS should be outermost)
    configure_security_headers(app)
    configure_cors(app)
    configure_rate_limiting(app)

    # Rate limit error handler
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        logger.warning(
            f"Rate limit exceeded for {request.client.host} on {request.url.path}"
        )
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded. Please try again later.",
                "retry_after": exc.detail,
            },
        )

    # Global exception handler (hide internal errors in production)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        
        if settings.debug:
            return JSONResponse(
                status_code=500,
                content={"detail": str(exc)},
            )
        
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred"},
        )

    # Include API routers
    app.include_router(api_router, prefix="/api/v1")

    # Root endpoint
    @app.get("/", include_in_schema=False)
    @limiter.limit("10/minute")
    async def root(request: Request):
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs" if settings.debug else "API documentation disabled",
        }

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )
    