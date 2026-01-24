"""
Secret database model.

Security considerations:
- Secret content is encrypted at rest (AES-256-GCM)
- Nonce stored alongside ciphertext (required for decryption)
- Foreign key to user ensures ownership
- Timestamps for audit trail
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Secret(Base):
    """Encrypted secret model."""

    __tablename__ = "secrets"

    # Primary key - UUID for security (non-sequential)
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Owner relationship
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Secret metadata (not encrypted - for display/search)
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Encrypted content
    encrypted_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Nonce/IV for AES-GCM (unique per encryption)
    nonce: Mapped[str] = mapped_column(
        String(24),  # Base64-encoded 12-byte nonce
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to user
    owner: Mapped["User"] = relationship(back_populates="secrets")

    def __repr__(self) -> str:
        return f"<Secret {self.name} (user={self.user_id})>"


# Import here to avoid circular imports
from app.models.user import User  # noqa: E402