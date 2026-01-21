"""
Security utilities and middleware configuration.

Implements:
- Security headers (similar to Helmet.js)
- CORS configuration
- Rate limiting setup
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

settings = get_settings()

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


def add_security_headers(response: Response) -> Response:
    """
    Add security headers to response.
    
    These headers protect against common web vulnerabilities:
    - XSS attacks
    - Clickjacking
    - MIME sniffing
    - Information disclosure
    """
    # Prevent XSS attacks
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    
    # HTTPS enforcement (enable in production)
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
    
    # Permissions Policy (formerly Feature-Policy)
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=()"
    )
    
    # Remove server identification
    if "server" in response.headers:
        del response.headers["server"]
    
    return response


async def security_headers_middleware(request: Request, call_next):
    """Middleware to add security headers to all responses."""
    response = await call_next(request)
    return add_security_headers(response)


def configure_cors(app: FastAPI) -> None:
    """
    Configure CORS with security-focused settings.
    
    Only allows:
    - Specific origins (no wildcards in production)
    - Credentials when needed
    - Limited HTTP methods
    - Limited headers
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
        ],
        expose_headers=["X-Request-ID"],
        max_age=600,  # Cache preflight for 10 minutes
    )


def configure_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting to prevent abuse."""
    app.state.limiter = limiter
