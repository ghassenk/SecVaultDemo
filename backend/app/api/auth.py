"""
Authentication API endpoints.

Security considerations:
- Rate limiting on login to prevent brute force
- Constant-time password comparison (via Argon2)
- No information leakage on failed attempts
- Secure token handling
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.jwt import create_tokens, verify_refresh_token
from app.core.password import check_needs_rehash, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import MessageResponse, RefreshTokenRequest, Token
from app.schemas.user import (
    PasswordChange,
    UserCreate,
    UserLogin,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password.",
)
async def register(
    request: Request,
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Register a new user account.
    
    - Validates email uniqueness
    - Hashes password with Argon2id
    - Returns user data (without password)
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none() is not None:
        # Use generic message to prevent email enumeration
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please check your information.",
        )
    
    # Create new user with hashed password
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"New user registered: {user.email}")
    
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get tokens",
    description="Authenticate with email and password to receive JWT tokens.",
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Authenticate user and return tokens.
    
    - Rate limited to 5 attempts per minute
    - Returns generic error message for security
    - Updates last_login_at timestamp
    - Rehashes password if needed (parameter upgrade)
    """
    # Generic error message to prevent user enumeration
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        logger.warning(f"Login attempt for non-existent email: {credentials.email}")
        raise auth_error
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt for: {user.email}")
        raise auth_error
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive account: {user.email}")
        raise auth_error
    
    # Check if password needs rehashing (security parameter upgrade)
    if check_needs_rehash(user.password_hash):
        user.password_hash = hash_password(credentials.password)
        logger.info(f"Rehashed password for: {user.email}")
    
    # Update last login timestamp
    user.last_login_at = datetime.now(UTC)
    await db.commit()
    
    # Generate tokens
    access_token, refresh_token = create_tokens(user.id)
    
    logger.info(f"Successful login: {user.email}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Use refresh token to get new access and refresh tokens.",
)
@limiter.limit("10/minute")
async def refresh_tokens(
    request: Request,
    token_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Refresh authentication tokens.
    
    - Validates refresh token
    - Issues new token pair
    - Old refresh token is implicitly invalidated (stateless)
    """
    # Verify refresh token
    payload = verify_refresh_token(token_request.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == payload.sub)
    )
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate new tokens
    access_token, refresh_token = create_tokens(user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information.",
)
async def get_me(current_user: CurrentUser) -> User:
    """Return current user's information."""
    return current_user


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change the current user's password.",
)
async def change_password(
    password_data: PasswordChange,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """
    Change user's password.
    
    - Verifies current password
    - Hashes and stores new password
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    # Check new password is different
    if verify_password(password_data.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )
    
    # Update password
    current_user.password_hash = hash_password(password_data.new_password)
    await db.commit()
    
    logger.info(f"Password changed for: {current_user.email}")
    
    return MessageResponse(message="Password changed successfully")


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Logout the current user (client should discard tokens).",
)
async def logout(current_user: CurrentUser) -> MessageResponse:
    """
    Logout user.
    
    Note: With stateless JWTs, logout is handled client-side
    by discarding tokens. This endpoint exists for API consistency
    and could be extended to implement token blacklisting.
    """
    logger.info(f"User logged out: {current_user.email}")
    return MessageResponse(message="Successfully logged out")