"""
Authentication dependencies for FastAPI routes.

Security considerations:
- Extracts and validates JWT from Authorization header
- Returns 401 for missing/invalid tokens
- Returns 403 for inactive users
- Provides current user to protected routes
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.jwt import verify_access_token
from app.models.user import User

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for JWT
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Extracts JWT from Authorization header, validates it,
    and returns the corresponding user.
    
    Raises:
        HTTPException 401: If token is missing or invalid
        HTTPException 403: If user is inactive
    """
    # Check for credentials
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the token
    token_payload = verify_access_token(credentials.credentials)
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == token_payload.sub)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        logger.warning(f"Token valid but user not found: {token_payload.sub}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency to get current active user.
    
    This is an alias for get_current_user that makes
    route definitions more readable.
    """
    return current_user


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_active_user)]