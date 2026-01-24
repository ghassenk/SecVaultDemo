"""
Encryption service using AES-256-GCM.

Security considerations:
- AES-256-GCM provides authenticated encryption (confidentiality + integrity)
- Unique nonce/IV for every encryption operation
- Key derivation using HKDF for per-user keys
- Master key from environment (production would use KMS)
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import get_settings

settings = get_settings()

# AES-256 requires 32-byte key
KEY_LENGTH = 32
# GCM recommended nonce size
NONCE_LENGTH = 12


def _get_master_key() -> bytes:
    """
    Get master encryption key from settings.
    
    In production, this should come from a KMS (AWS KMS, HashiCorp Vault, etc.)
    """
    key = settings.encryption_master_key.encode('utf-8')
    # If key is hex-encoded, decode it
    if len(key) == 64:
        try:
            return bytes.fromhex(settings.encryption_master_key)
        except ValueError:
            pass
    # Otherwise, derive a proper key from the provided secret
    return _derive_key(key, b"master-key-derivation")


def _derive_key(input_key: bytes, context: bytes) -> bytes:
    """
    Derive a cryptographic key using HKDF.
    
    Args:
        input_key: Input key material
        context: Context/info for key derivation (e.g., user_id)
        
    Returns:
        32-byte derived key suitable for AES-256
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=None,  # HKDF can work without salt
        info=context,
    )
    return hkdf.derive(input_key)


def derive_user_key(user_id: str) -> bytes:
    """
    Derive a unique encryption key for a user.
    
    Each user gets their own derived key, so compromising one
    user's data doesn't affect others.
    
    Args:
        user_id: User's unique identifier
        
    Returns:
        32-byte key unique to this user
    """
    master_key = _get_master_key()
    context = f"user-key:{user_id}".encode('utf-8')
    return _derive_key(master_key, context)


def encrypt(plaintext: str, user_id: str) -> tuple[str, str]:
    """
    Encrypt plaintext using AES-256-GCM.
    
    Args:
        plaintext: Text to encrypt
        user_id: User ID for key derivation
        
    Returns:
        Tuple of (base64_ciphertext, base64_nonce)
    """
    # Derive user-specific key
    key = derive_user_key(user_id)
    
    # Generate random nonce (NEVER reuse with same key)
    nonce = os.urandom(NONCE_LENGTH)
    
    # Encrypt
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(
        nonce,
        plaintext.encode('utf-8'),
        None,  # Additional authenticated data (AAD) - not used here
    )
    
    # Encode to base64 for storage
    return (
        base64.b64encode(ciphertext).decode('utf-8'),
        base64.b64encode(nonce).decode('utf-8'),
    )


def decrypt(ciphertext_b64: str, nonce_b64: str, user_id: str) -> str:
    """
    Decrypt ciphertext using AES-256-GCM.
    
    Args:
        ciphertext_b64: Base64-encoded ciphertext (includes GCM auth tag)
        nonce_b64: Base64-encoded nonce
        user_id: User ID for key derivation
        
    Returns:
        Decrypted plaintext
        
    Raises:
        ValueError: If decryption fails (tampered data or wrong key)
    """
    # Derive user-specific key
    key = derive_user_key(user_id)
    
    # Decode from base64
    ciphertext = base64.b64decode(ciphertext_b64)
    nonce = base64.b64decode(nonce_b64)
    
    # Decrypt and verify integrity
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError("Decryption failed: data may be tampered or corrupted") from e


def rotate_encryption(
    old_ciphertext_b64: str,
    old_nonce_b64: str,
    user_id: str,
) -> tuple[str, str]:
    """
    Re-encrypt data with a new nonce.
    
    Useful for key rotation or periodic re-encryption.
    
    Args:
        old_ciphertext_b64: Existing ciphertext
        old_nonce_b64: Existing nonce
        user_id: User ID
        
    Returns:
        Tuple of (new_ciphertext_b64, new_nonce_b64)
    """
    # Decrypt with old nonce
    plaintext = decrypt(old_ciphertext_b64, old_nonce_b64, user_id)
    # Re-encrypt with new nonce
    return encrypt(plaintext, user_id)