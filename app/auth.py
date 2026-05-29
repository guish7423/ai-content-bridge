"""Auth utilities — password hashing, JWT tokens, API key management."""
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt  # type: ignore[import-untyped]

from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-SHA256 (pure Python, no native deps)."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
    return f"$pbkdf2-sha256$600000${salt.hex()}${key.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash (PBKDF2-SHA256)."""
    try:
        parts = hashed.split("$")
        if parts[1] != "pbkdf2-sha256":
            return False
        iterations = int(parts[2])
        salt = bytes.fromhex(parts[3])
        expected = bytes.fromhex(parts[4])
        key = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(key, expected)
    except (IndexError, ValueError, AttributeError):
        return False


def create_access_token(user_id: int, email: str) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token. Returns payload or None."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.DecodeError):
        return None


def generate_api_key() -> str:
    """Generate a unique API key (can use as Bearer token)."""
    return "acb_" + secrets.token_hex(32)


def verify_api_key(key: str) -> bool:
    """Verify an API key format."""
    return key.startswith("acb_") and len(key) == 69  # 4 + 64 hex chars + _


def get_bearer_token_from_header(auth_header: str | None) -> str | None:
    """Extract bearer token from Authorization header."""
    if not auth_header:
        return None
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None
