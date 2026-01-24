"""
Secret Pydantic schemas for request/response validation.

Security considerations:
- Encrypted content never exposed in responses
- Decrypted content only in specific response types
- Strict validation on all inputs
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SecretBase(BaseModel):
    """Base secret schema with common fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name/title of the secret",
        examples=["AWS API Key", "Database Password"],
    )

    description: str | None = Field(
        None,
        max_length=500,
        description="Optional description",
        examples=["Production AWS credentials"],
    )


class SecretCreate(SecretBase):
    """Schema for creating a new secret."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Secret content to encrypt",
        examples=["AKIAIOSFODNN7EXAMPLE"],
    )


class SecretUpdate(BaseModel):
    """Schema for updating a secret."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="New name for the secret",
    )

    description: str | None = Field(
        None,
        max_length=500,
        description="New description",
    )

    content: str | None = Field(
        None,
        min_length=1,
        max_length=10000,
        description="New secret content (will be re-encrypted)",
    )


class SecretResponse(SecretBase):
    """Schema for secret responses (without decrypted content)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Secret ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SecretWithContent(SecretResponse):
    """Schema for secret response with decrypted content."""

    content: str = Field(..., description="Decrypted secret content")


class SecretList(BaseModel):
    """Schema for paginated secret list."""

    items: list[SecretResponse] = Field(..., description="List of secrets")
    total: int = Field(..., description="Total number of secrets")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")