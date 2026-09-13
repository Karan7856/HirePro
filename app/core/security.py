"""Password hashing and verification using bcrypt via passlib.

Only hashing/verification lives here for now.
JWT creation and decoding will be added in a later module.
"""

from passlib.context import CryptContext

# Single bcrypt context for the whole application.
# schemes=["bcrypt"] means only bcrypt hashes are accepted/produced.
# deprecated="auto" marks any non-preferred scheme as deprecated automatically.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password*.

    The resulting string is safe to store in the database.
    It is never identical to the original password.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password*.

    Uses constant-time comparison internally to prevent timing attacks.
    Returns False for any mismatch, including malformed hash strings.
    """
    return _pwd_context.verify(plain_password, hashed_password)
