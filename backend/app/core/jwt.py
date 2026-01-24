"""
JWT token service for authentication.

Security considerations:
- Short-lived access tokens (15 min default)
- Longer-lived refresh tokens (7 days default)
- Tokens include type claim to prevent misuse
- Secure secret key from environment
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import get_settings
from app.schemas.auth import TokenPayload

settings = get_settings()


def create_access_token(user_id: str) -> str:
    """
    Create a short-lived access token.
    
    Args:
        user_id: User's unique identifier
        
    Returns:
        Encoded JWT access token
    """
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: str) -> str:
    """
    Create a longer-lived refresh token.
    
    Args:
        user_id: User's unique identifier
        
    Returns:
        Encoded JWT refresh token
    """
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "refresh",
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_tokens(user_id: str) -> tuple[str, str]:
    """
    Create both access and refresh tokens.
    
    Args:
        user_id: User's unique identifier
        
    Returns:
        Tuple of (access_token, refresh_token)
    """
    return create_access_token(user_id), create_refresh_token(user_id)


def decode_token(token: str) -> TokenPayload | None:
    """
    Decode and validate a JWT token.
    
    Args:
        token: Encoded JWT token
        
    Returns:
        TokenPayload if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except JWTError:
        return None


def verify_access_token(token: str) -> TokenPayload | None:
    """
    Verify an access token is valid and of correct type.
    
    Args:
        token: Encoded JWT access token
        
    Returns:
        TokenPayload if valid access token, None otherwise
    """
    payload = decode_token(token)
    if payload is None or payload.type != "access":
        return None
    return payload


def verify_refresh_token(token: str) -> TokenPayload | None:
    """
    Verify a refresh token is valid and of correct type.
    
    Args:
        token: Encoded JWT refresh token
        
    Returns:
        TokenPayload if valid refresh token, None otherwise
    """
    payload = decode_token(token)
    if payload is None or payload.type != "refresh":
        return None
    return payload