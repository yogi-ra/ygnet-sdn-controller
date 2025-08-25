from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
import jwt  # Using PyJWT
from cryptography.fernet import Fernet
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Generate a key for encryption. In a real app, load this from config/secrets management.
# For this example, we'll derive it from the SECRET_KEY for simplicity.
# IMPORTANT: If SECRET_KEY changes, all encrypted data will be unreadable.
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64

digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
digest.update(settings.SECRET_KEY.encode())

if settings.SECRET_KEY == "your_super_secret_key_change_me":
    raise ValueError("SECRET_KEY must be set in .env and not be the default value.")

key = base64.urlsafe_b64encode(digest.finalize())
fernet = Fernet(key)

# --- Password Hashing for Users ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# --- Data Encryption for Device Credentials ---
def encrypt_data(data: str) -> str:
    """Encrypts a string."""
    if not data:
        return None
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> Optional[str]:
    """Decrypts a string. Returns None if decryption fails."""
    if not encrypted_data:
        return None
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logger.error(f"Failed to decrypt data: {e}")
        return None


# --- JWT Token Handling ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    # Note: PyJWT.encode returns a string directly
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
