"""
Application configuration with security-focused defaults.

Security considerations:
- All secrets loaded from environment variables
- Strict validation of configuration values
- Secure defaults for all security-related settings
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "SecureVault"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: str = Field(default="http://localhost:3000")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://securevault:securevault@db:5432/securevault"
    )

    # Security - JWT
    jwt_secret_key: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT signing. Must be at least 32 characters.",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)

    # Security - Encryption
    encryption_master_key: str = Field(
        ...,
        min_length=32,
        description="Master key for AES-256 encryption. Must be at least 32 characters.",
    )

    # Security - Password Hashing (Argon2id parameters)
    argon2_time_cost: int = Field(default=3, ge=1)
    argon2_memory_cost: int = Field(default=65536, ge=8192)  # 64 MB
    argon2_parallelism: int = Field(default=4, ge=1)

    # Security - Rate Limiting
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)

    # Security - Miscellaneous
    bcrypt_rounds: int = Field(default=12, ge=10, le=15)

    @field_validator("jwt_secret_key", "encryption_master_key")
    @classmethod
    def validate_secret_strength(cls, v: str, info) -> str:
        """Ensure secrets meet minimum security requirements."""
        if len(v) < 32:
            raise ValueError(
                f"{info.field_name} must be at least 32 characters for security"
            )
        return v

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse allowed_origins as a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
