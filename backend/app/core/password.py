"""
Password hashing service using Argon2id.

Security considerations:
- Argon2id is the recommended algorithm (PHC winner)
- Memory-hard to resist GPU/ASIC attacks
- Configurable parameters for security/performance tradeoff
- Constant-time comparison to prevent timing attacks
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

settings = get_settings()

# Configure Argon2id hasher with settings from config
# These parameters should be tuned based on your server capabilities
# Higher values = more secure but slower
password_hasher = PasswordHasher(
    time_cost=settings.argon2_time_cost,      # Number of iterations
    memory_cost=settings.argon2_memory_cost,  # Memory usage in KiB
    parallelism=settings.argon2_parallelism,  # Number of parallel threads
    hash_len=32,                               # Length of the hash in bytes
    salt_len=16,                               # Length of random salt in bytes
)


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2id.
    
    Args:
        password: Plain text password
        
    Returns:
        Argon2id hash string (includes algorithm, params, salt, and hash)
    """
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Uses constant-time comparison to prevent timing attacks.
    
    Args:
        password: Plain text password to verify
        password_hash: Stored Argon2id hash
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        password_hasher.verify(password_hash, password)
        return True
    except (VerificationError, InvalidHashError):
        return False


def check_needs_rehash(password_hash: str) -> bool:
    """
    Check if a password hash needs to be rehashed.
    
    This is useful when upgrading security parameters.
    After verifying a password, check if the hash uses
    outdated parameters and rehash if necessary.
    
    Args:
        password_hash: Stored Argon2id hash
        
    Returns:
        True if hash should be regenerated with current parameters
    """
    return password_hasher.check_needs_rehash(password_hash)