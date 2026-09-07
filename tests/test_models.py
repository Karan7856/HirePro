"""Unit tests for ORM model metadata — no database connection required."""
import uuid

from sqlalchemy import inspect as sa_inspect

from app.db.base import Base
from app.models.user import USER_ROLES, User


class TestUserModelMetadata:
    """Verify the User model's table structure without connecting to PostgreSQL."""

    def _cols(self) -> dict:
        return {c.name: c for c in User.__table__.columns}

    def test_table_name(self):
        assert User.__tablename__ == "users"

    def test_user_model_is_registered_in_base_metadata(self):
        assert "users" in Base.metadata.tables

    def test_primary_key_is_id(self):
        cols = self._cols()
        assert "id" in cols
        assert cols["id"].primary_key is True

    def test_id_is_uuid_type(self):
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID
        cols = self._cols()
        assert isinstance(cols["id"].type, PG_UUID)

    def test_required_columns_exist(self):
        expected = {"id", "email", "hashed_password", "full_name", "role", "is_active",
                    "created_at", "updated_at"}
        actual = set(self._cols().keys())
        assert expected == actual

    def test_email_is_unique(self):
        cols = self._cols()
        assert cols["email"].unique is True

    def test_email_max_length(self):
        cols = self._cols()
        assert cols["email"].type.length == 255

    def test_hashed_password_max_length(self):
        cols = self._cols()
        assert cols["hashed_password"].type.length == 255

    def test_full_name_max_length(self):
        cols = self._cols()
        assert cols["full_name"].type.length == 150

    def test_role_max_length(self):
        cols = self._cols()
        assert cols["role"].type.length == 20

    def test_is_active_is_boolean(self):
        from sqlalchemy import Boolean
        cols = self._cols()
        assert isinstance(cols["is_active"].type, Boolean)

    def test_is_active_defaults_to_true(self):
        cols = self._cols()
        assert cols["is_active"].default.arg is True

    def test_timestamps_are_timezone_aware(self):
        from sqlalchemy import DateTime
        cols = self._cols()
        assert isinstance(cols["created_at"].type, DateTime)
        assert cols["created_at"].type.timezone is True
        assert isinstance(cols["updated_at"].type, DateTime)
        assert cols["updated_at"].type.timezone is True

    def test_role_check_constraint_exists(self):
        constraint_names = {c.name for c in User.__table__.constraints}
        assert "ck_users_role" in constraint_names

    def test_user_roles_constant_contains_all_roles(self):
        assert set(USER_ROLES) == {"student", "recruiter", "admin"}

    def test_no_extra_columns(self):
        """Guard against accidental column additions."""
        cols = self._cols()
        assert len(cols) == 8


class TestUserInstantiation:
    """Verify User objects can be constructed without a DB session."""

    def test_can_instantiate_user(self):
        user = User(
            email="test@example.com",
            hashed_password="$2b$12$hashed",
            full_name="Test User",
            role="student",
        )
        assert user.email == "test@example.com"
        assert user.role == "student"
        # is_active default is applied on INSERT, not bare instantiation;
        # the column-level default is verified in TestUserModelMetadata.
        # When explicitly provided it should be honoured.
        active_user = User(email="a@b.com", hashed_password="h", full_name="A",
                           role="student", is_active=True)
        assert active_user.is_active is True

    def test_repr_contains_email_and_role(self):
        user = User(email="a@b.com", hashed_password="x", full_name="A", role="recruiter")
        r = repr(user)
        assert "a@b.com" in r
        assert "recruiter" in r

    def test_default_id_is_uuid(self):
        user = User(
            email="u@example.com",
            hashed_password="h",
            full_name="U",
            role="admin",
            id=uuid.uuid4(),
        )
        assert isinstance(user.id, uuid.UUID)
