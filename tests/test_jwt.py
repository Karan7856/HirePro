"""Unit tests for JWT creation and decoding in app.core.security."""

import uuid
from datetime import timedelta

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_user_id_from_token,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(
    user_id: uuid.UUID | None = None,
    role: str = "student",
    expires_delta: timedelta | None = None,
) -> str:
    uid = user_id or uuid.uuid4()
    return create_access_token(uid, role, expires_delta=expires_delta)


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

class TestCreateAccessToken:

    def test_returns_non_empty_string(self):
        token = _make_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_is_three_dot_separated_segments(self):
        # All JWTs have exactly three base64url segments separated by dots.
        token = _make_token()
        assert token.count(".") == 2

    def test_different_users_produce_different_tokens(self):
        t1 = _make_token(user_id=uuid.uuid4())
        t2 = _make_token(user_id=uuid.uuid4())
        assert t1 != t2

    def test_same_user_called_twice_may_differ(self):
        # iat is included; rapid successive calls in the same second may
        # produce the same token, but the function must not error.
        uid = uuid.uuid4()
        t1 = create_access_token(uid, "student")
        t2 = create_access_token(uid, "student")
        assert isinstance(t1, str)
        assert isinstance(t2, str)

    def test_roles_reflected_in_separate_tokens(self):
        uid = uuid.uuid4()
        t_student = create_access_token(uid, "student")
        t_recruiter = create_access_token(uid, "recruiter")
        p_student = decode_access_token(t_student)
        p_recruiter = decode_access_token(t_recruiter)
        assert p_student["role"] == "student"
        assert p_recruiter["role"] == "recruiter"


# ---------------------------------------------------------------------------
# Required claims
# ---------------------------------------------------------------------------

class TestTokenClaims:

    def test_sub_claim_present(self):
        payload = decode_access_token(_make_token())
        assert "sub" in payload

    def test_sub_claim_prefixed_with_user(self):
        payload = decode_access_token(_make_token())
        assert payload["sub"].startswith("user:")

    def test_sub_claim_contains_user_uuid(self):
        uid = uuid.uuid4()
        payload = decode_access_token(create_access_token(uid, "student"))
        sub = payload["sub"]
        extracted = uuid.UUID(sub[len("user:"):])
        assert extracted == uid

    def test_role_claim_present(self):
        payload = decode_access_token(_make_token(role="recruiter"))
        assert payload.get("role") == "recruiter"

    def test_exp_claim_present(self):
        payload = decode_access_token(_make_token())
        assert "exp" in payload

    def test_iat_claim_present(self):
        payload = decode_access_token(_make_token())
        assert "iat" in payload

    def test_exp_is_after_iat(self):
        payload = decode_access_token(_make_token())
        assert payload["exp"] > payload["iat"]

    def test_all_three_roles_accepted(self):
        for role in ("student", "recruiter", "admin"):
            payload = decode_access_token(_make_token(role=role))
            assert payload["role"] == role


# ---------------------------------------------------------------------------
# Successful decoding / identity extraction
# ---------------------------------------------------------------------------

class TestDecodeAccessToken:

    def test_decode_returns_dict(self):
        result = decode_access_token(_make_token())
        assert isinstance(result, dict)

    def test_round_trip_user_id(self):
        uid = uuid.uuid4()
        token = create_access_token(uid, "admin")
        extracted = get_user_id_from_token(token)
        assert extracted == uid

    def test_get_user_id_returns_uuid_instance(self):
        uid = uuid.uuid4()
        result = get_user_id_from_token(create_access_token(uid, "student"))
        assert isinstance(result, uuid.UUID)


# ---------------------------------------------------------------------------
# Invalid / malformed token rejection
# ---------------------------------------------------------------------------

class TestInvalidTokenRejection:

    def test_empty_string_raises(self):
        with pytest.raises(JWTError):
            decode_access_token("")

    def test_random_string_raises(self):
        with pytest.raises(JWTError):
            decode_access_token("not.a.token")

    def test_tampered_signature_raises(self):
        token = _make_token()
        # Flip the last character to corrupt the signature segment.
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(JWTError):
            decode_access_token(tampered)

    def test_wrong_secret_raises(self):
        from jose import jwt as jose_jwt
        import uuid as _uuid
        from datetime import datetime, timezone, timedelta
        payload = {
            "sub": f"user:{_uuid.uuid4()}",
            "role": "student",
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=30),
        }
        token_wrong_secret = jose_jwt.encode(payload, "WRONG_SECRET", algorithm="HS256")
        with pytest.raises(JWTError):
            decode_access_token(token_wrong_secret)

    def test_missing_sub_claim_raises(self):
        from jose import jwt as jose_jwt
        from datetime import datetime, timezone, timedelta
        from app.core.config import settings as _settings
        payload = {
            "role": "student",
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=30),
        }
        token = jose_jwt.encode(payload, _settings.JWT_SECRET_KEY, algorithm="HS256")
        with pytest.raises(JWTError):
            decode_access_token(token)

    def test_sub_without_prefix_raises(self):
        from jose import jwt as jose_jwt
        from datetime import datetime, timezone, timedelta
        from app.core.config import settings as _settings
        payload = {
            "sub": str(uuid.uuid4()),  # missing "user:" prefix
            "role": "student",
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=30),
        }
        token = jose_jwt.encode(payload, _settings.JWT_SECRET_KEY, algorithm="HS256")
        with pytest.raises(JWTError):
            decode_access_token(token)


# ---------------------------------------------------------------------------
# Expiry behaviour
# ---------------------------------------------------------------------------

class TestTokenExpiry:

    def test_expired_token_raises(self):
        # Create a token that expired 1 second ago.
        token = create_access_token(
            uuid.uuid4(), "student", expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(JWTError):
            decode_access_token(token)

    def test_custom_expiry_accepted_while_valid(self):
        # A token with a generous lifetime should decode without error.
        token = create_access_token(
            uuid.uuid4(), "student", expires_delta=timedelta(hours=1)
        )
        payload = decode_access_token(token)
        assert "sub" in payload

    def test_very_short_but_not_expired_token_is_valid(self):
        token = create_access_token(
            uuid.uuid4(), "student", expires_delta=timedelta(seconds=60)
        )
        payload = decode_access_token(token)
        assert payload["role"] == "student"
