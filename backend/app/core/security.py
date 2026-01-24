"""
Security utilities and middleware configuration.

Implements:
- Security headers (similar to Helmet.js)
- CORS configuration
- Rate limiting setup
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import get_settings

settings = get_settings()

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


class SecurityHeadersMiddleware:
    """
    Pure ASGI middleware for adding security headers.
    
    This avoids the event loop issues that come with BaseHTTPMiddleware.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Security headers
                security_headers = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"x-xss-protection", b"1; mode=block"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"permissions-policy", b"geolocation=(), microphone=(), camera=(), payment=(), usb=()"),
                    (b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"),
                ]
                
                # Add HSTS in production
                if settings.environment == "production":
                    security_headers.append(
                        (b"strict-transport-security", b"max-age=31536000; includeSubDomains; preload")
                    )
                
                # Merge with existing headers
                existing_headers = list(message.get("headers", []))
                existing_headers.extend(security_headers)
                message["headers"] = existing_headers

            await send(message)

        await self.app(scope, receive, send_with_headers)


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
        allow_origins=settings.allowed_origins_list,
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


def configure_security_headers(app: FastAPI) -> None:
    """Add security headers middleware."""
    app.add_middleware(SecurityHeadersMiddleware)


def configure_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting to prevent abuse."""
    app.state.limiter = limiter
    