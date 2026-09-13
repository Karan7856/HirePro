"""Unit tests for app.core.security — password hashing and verification."""

import pytest

from app.core.security import hash_password, verify_password


class TestHashPassword:

    def test_hash_differs_from_plain(self):
        hashed = hash_password("mysecretpassword")
        assert hashed != "mysecretpassword"

    def test_hash_is_non_empty_string(self):
        hashed = hash_password("anypassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_looks_like_bcrypt(self):
        # bcrypt hashes always start with $2b$ (or $2a$ on some implementations).
        hashed = hash_password("testpass")
        assert hashed.startswith("$2")

    def test_same_password_produces_different_hashes(self):
        # bcrypt uses a random salt on every call — two hashes of the same
        # password must not be identical strings.
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2

    def test_different_passwords_produce_different_hashes(self):
        h1 = hash_password("password_one")
        h2 = hash_password("password_two")
        assert h1 != h2


class TestVerifyPassword:

    def test_correct_password_verifies(self):
        hashed = hash_password("correcthorsebatterystaple")
        assert verify_password("correcthorsebatterystaple", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_string_fails_against_non_empty_hash(self):
        hashed = hash_password("somepassword")
        assert verify_password("", hashed) is False

    def test_correct_password_after_multiple_hashes(self):
        # Both hashes of the same password must verify correctly against
        # the original plain-text, even though the hash strings differ.
        plain = "multihashedpassword"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert verify_password(plain, h1) is True
        assert verify_password(plain, h2) is True

    def test_cross_password_does_not_verify(self):
        h1 = hash_password("alpha")
        h2 = hash_password("beta")
        assert verify_password("alpha", h2) is False
        assert verify_password("beta", h1) is False

    def test_case_sensitive_verification(self):
        hashed = hash_password("Password123")
        assert verify_password("password123", hashed) is False
        assert verify_password("PASSWORD123", hashed) is False
        assert verify_password("Password123", hashed) is True
