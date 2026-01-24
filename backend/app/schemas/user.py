"""
User Pydantic schemas for request/response validation.

Security considerations:
- Password never included in responses
- Email normalized to lowercase
- Strict validation on all inputs
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="User password (min 12 characters)",
        examples=["SecureP@ssw0rd!"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets security requirements.
        
        Requirements:
        - At least 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")

        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")

        special_chars = set("!@#$%^&*()_+-=[]{}|;':\",./<>?`~")
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character")

        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(
        ...,
        description="User email address",
    )
    password: str = Field(
        ...,
        description="User password",
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()


class UserResponse(UserBase):
    """Schema for user responses (no sensitive data)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User ID")
    is_active: bool = Field(..., description="Account active status")
    is_verified: bool = Field(..., description="Email verification status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login_at: datetime | None = Field(None, description="Last login timestamp")


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    email: EmailStr | None = Field(None, description="New email address")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        """Normalize email to lowercase."""
        if v is None:
            return None
        return v.lower().strip()


class PasswordChange(BaseModel):
    """Schema for changing password."""

    current_password: str = Field(
        ...,
        description="Current password",
    )
    new_password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="New password (min 12 characters)",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate new password meets security requirements."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")

        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")

        special_chars = set("!@#$%^&*()_+-=[]{}|;':\",./<>?`~")
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character")

        return v