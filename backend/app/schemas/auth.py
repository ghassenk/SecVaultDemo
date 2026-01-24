"""
Authentication Pydantic schemas.

Schemas for JWT tokens and authentication responses.
"""

from pydantic import BaseModel, Field


class Token(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenPayload(BaseModel):
    """JWT token payload (decoded)."""

    sub: str = Field(..., description="Subject (user ID)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    type: str = Field(..., description="Token type (access/refresh)")


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""

    refresh_token: str = Field(..., description="Refresh token")


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Response message")