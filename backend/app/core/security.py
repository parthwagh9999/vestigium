"""JWT authentication and password hashing utilities.

Provides token creation, validation, and bcrypt password hashing
for the authentication system.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt

from app.config import Settings


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt hash string.
    """
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: The plaintext password to check.
        hashed_password: The bcrypt hash to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    pwd_bytes = plain_password.encode("utf-8")
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    subject: str,
    settings: Settings,
    additional_claims: dict | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The token subject (typically user ID).
        settings: Application settings for JWT configuration.
        additional_claims: Optional additional claims to include.

    Returns:
        Encoded JWT access token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str,
    settings: Settings,
) -> str:
    """Create a JWT refresh token with longer expiry.

    Args:
        subject: The token subject (typically user ID).
        settings: Application settings for JWT configuration.

    Returns:
        Encoded JWT refresh token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: Settings) -> dict:
    """Decode and validate a JWT token.

    Args:
        token: The encoded JWT token string.
        settings: Application settings for JWT configuration.

    Returns:
        The decoded token payload as a dictionary.

    Raises:
        JWTError: If the token is invalid, expired, or tampered with.
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


class TokenValidationError(Exception):
    """Raised when a JWT token fails validation."""

    def __init__(self, message: str = "Invalid or expired token") -> None:
        self.message = message
        super().__init__(self.message)


def validate_access_token(token: str, settings: Settings) -> str:
    """Validate an access token and return the subject (user ID).

    Args:
        token: The encoded JWT access token.
        settings: Application settings.

    Returns:
        The user ID from the token subject.

    Raises:
        TokenValidationError: If the token is invalid or not an access token.
    """
    try:
        payload = decode_token(token, settings)
    except JWTError as e:
        raise TokenValidationError(f"Token validation failed: {e}") from e

    if payload.get("type") != "access":
        raise TokenValidationError("Token is not an access token")

    subject = payload.get("sub")
    if not subject:
        raise TokenValidationError("Token has no subject")

    return subject


def validate_refresh_token(token: str, settings: Settings) -> str:
    """Validate a refresh token and return the subject (user ID).

    Args:
        token: The encoded JWT refresh token.
        settings: Application settings.

    Returns:
        The user ID from the token subject.

    Raises:
        TokenValidationError: If the token is invalid or not a refresh token.
    """
    try:
        payload = decode_token(token, settings)
    except JWTError as e:
        raise TokenValidationError(f"Token validation failed: {e}") from e

    if payload.get("type") != "refresh":
        raise TokenValidationError("Token is not a refresh token")

    subject = payload.get("sub")
    if not subject:
        raise TokenValidationError("Token has no subject")

    return subject
