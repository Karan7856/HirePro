"""Password hashing/verification and JWT creation/decoding.

Password hashing uses bcrypt via passlib.
JWT uses python-jose with HS256 (configurable via settings).

Only create_access_token() and decode_access_token() live here for now.
OAuth2 route dependencies will be added in a later module.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

# Single bcrypt context for the whole application.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password*.

    Safe to store in the database; never identical to the original password.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password*.

    Uses constant-time comparison internally to prevent timing attacks.
    """
    return _pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

# The standard claim used to carry the authenticated user's identity.
# We use the string form of the user UUID as the subject ("sub") claim.
_SUB_PREFIX = "user:"


def create_access_token(
    user_id: uuid.UUID,
    role: str,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for *user_id*.

    Claims included:
    - sub  : "user:<uuid>"  — uniquely identifies the user
    - role : user's role string (student / recruiter / admin)
    - exp  : expiry timestamp (UTC)
    - iat  : issued-at timestamp (UTC)

    Args:
        user_id:       The user's UUID from the database.
        role:          The user's role string.
        expires_delta: Optional override for token lifetime.
                       Defaults to settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        A signed JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = now + expires_delta

    payload: dict[str, Any] = {
        "sub": f"{_SUB_PREFIX}{user_id}",
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Validates the signature, expiry, and the presence of the "sub" claim.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload dict.

    Raises:
        JWTError: If the token is invalid, malformed, or expired.
                  Callers convert this into an HTTP 401 response.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    sub: str | None = payload.get("sub")
    if sub is None or not sub.startswith(_SUB_PREFIX):
        raise JWTError("Token missing required 'sub' claim")
    return payload


def get_user_id_from_token(token: str) -> uuid.UUID:
    """Convenience wrapper: decode a token and return the user UUID.

    Raises:
        JWTError: propagated from decode_access_token() on any failure.
        ValueError: if the UUID portion of the sub claim is not a valid UUID.
    """
    payload = decode_access_token(token)
    sub: str = payload["sub"]
    raw_id = sub[len(_SUB_PREFIX):]
    return uuid.UUID(raw_id)
