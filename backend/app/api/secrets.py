"""
Secrets API endpoints.

Security considerations:
- All endpoints require authentication
- Row-level access control (users only see their own secrets)
- Content encrypted before storage, decrypted on retrieval
- Pagination to prevent data dumps
"""

import logging
import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.encryption import decrypt, encrypt
from app.models.secret import Secret
from app.schemas.auth import MessageResponse
from app.schemas.secret import (
    SecretCreate,
    SecretList,
    SecretResponse,
    SecretUpdate,
    SecretWithContent,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/secrets", tags=["Secrets"])


@router.post(
    "",
    response_model=SecretResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new secret",
    description="Create a new encrypted secret for the current user.",
)
async def create_secret(
    secret_data: SecretCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Secret:
    """
    Create a new secret.
    
    - Encrypts content with user-specific key
    - Stores encrypted data and nonce
    """
    # Encrypt the secret content
    encrypted_content, nonce = encrypt(secret_data.content, current_user.id)
    
    # Create secret record
    secret = Secret(
        user_id=current_user.id,
        name=secret_data.name,
        description=secret_data.description,
        encrypted_content=encrypted_content,
        nonce=nonce,
    )
    
    db.add(secret)
    await db.commit()
    await db.refresh(secret)
    
    logger.info(f"Secret created: {secret.id} for user {current_user.email}")
    
    return secret


@router.get(
    "",
    response_model=SecretList,
    summary="List all secrets",
    description="Get a paginated list of the current user's secrets.",
)
async def list_secrets(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
) -> SecretList:
    """
    List user's secrets with pagination.
    
    - Only returns metadata, not decrypted content
    - Ordered by creation date (newest first)
    """
    # Count total secrets for this user
    count_query = select(func.count(Secret.id)).where(Secret.user_id == current_user.id)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Calculate pagination
    pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    
    # Fetch secrets
    query = (
        select(Secret)
        .where(Secret.user_id == current_user.id)
        .order_by(Secret.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    secrets = result.scalars().all()
    
    return SecretList(
        items=secrets,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{secret_id}",
    response_model=SecretWithContent,
    summary="Get a secret",
    description="Get a specific secret with decrypted content.",
)
async def get_secret(
    secret_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SecretWithContent:
    """
    Get a secret with decrypted content.
    
    - Verifies ownership before returning
    - Decrypts content with user-specific key
    """
    # Fetch secret
    result = await db.execute(
        select(Secret).where(Secret.id == secret_id)
    )
    secret = result.scalar_one_or_none()
    
    # Check existence
    if secret is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )
    
    # Check ownership (row-level access control)
    if secret.user_id != current_user.id:
        logger.warning(
            f"Unauthorized access attempt: user {current_user.id} tried to access secret {secret_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",  # Don't reveal it exists
        )
    
    # Decrypt content
    try:
        decrypted_content = decrypt(
            secret.encrypted_content,
            secret.nonce,
            current_user.id,
        )
    except ValueError as e:
        logger.error(f"Decryption failed for secret {secret_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt secret",
        )
    
    return SecretWithContent(
        id=secret.id,
        name=secret.name,
        description=secret.description,
        content=decrypted_content,
        created_at=secret.created_at,
        updated_at=secret.updated_at,
    )


@router.put(
    "/{secret_id}",
    response_model=SecretResponse,
    summary="Update a secret",
    description="Update a secret's metadata and/or content.",
)
async def update_secret(
    secret_id: str,
    secret_data: SecretUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Secret:
    """
    Update a secret.
    
    - Verifies ownership before updating
    - Re-encrypts content if provided
    """
    # Fetch secret
    result = await db.execute(
        select(Secret).where(Secret.id == secret_id)
    )
    secret = result.scalar_one_or_none()
    
    # Check existence
    if secret is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )
    
    # Check ownership
    if secret.user_id != current_user.id:
        logger.warning(
            f"Unauthorized update attempt: user {current_user.id} tried to update secret {secret_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )
    
    # Update fields
    if secret_data.name is not None:
        secret.name = secret_data.name
    
    if secret_data.description is not None:
        secret.description = secret_data.description
    
    # Re-encrypt content if provided
    if secret_data.content is not None:
        encrypted_content, nonce = encrypt(secret_data.content, current_user.id)
        secret.encrypted_content = encrypted_content
        secret.nonce = nonce
    
    await db.commit()
    await db.refresh(secret)
    
    logger.info(f"Secret updated: {secret_id} by user {current_user.email}")
    
    return secret


@router.delete(
    "/{secret_id}",
    response_model=MessageResponse,
    summary="Delete a secret",
    description="Permanently delete a secret.",
)
async def delete_secret(
    secret_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """
    Delete a secret.
    
    - Verifies ownership before deleting
    - Permanent deletion (no soft delete)
    """
    # Fetch secret
    result = await db.execute(
        select(Secret).where(Secret.id == secret_id)
    )
    secret = result.scalar_one_or_none()
    
    # Check existence
    if secret is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )
    
    # Check ownership
    if secret.user_id != current_user.id:
        logger.warning(
            f"Unauthorized delete attempt: user {current_user.id} tried to delete secret {secret_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )
    
    # Delete
    await db.delete(secret)
    await db.commit()
    
    logger.info(f"Secret deleted: {secret_id} by user {current_user.email}")
    
    return MessageResponse(message="Secret deleted successfully")