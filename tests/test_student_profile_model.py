"""Unit tests for the StudentProfile ORM model — no database connection required."""
import uuid
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base
from app.models.student_profile import StudentProfile


class TestStudentProfileMetadata:

    def _cols(self) -> dict:
        return {c.name: c for c in StudentProfile.__table__.columns}

    def test_table_name(self):
        assert StudentProfile.__tablename__ == "student_profiles"

    def test_registered_in_base_metadata(self):
        assert "student_profiles" in Base.metadata.tables

    def test_required_columns_exist(self):
        expected = {
            "id", "user_id", "phone", "date_of_birth", "bio",
            "resume_content", "current_gpa", "graduation_year",
            "created_at", "updated_at",
        }
        assert set(self._cols().keys()) == expected

    def test_no_extra_columns(self):
        assert len(self._cols()) == 10

    def test_primary_key_is_id(self):
        assert self._cols()["id"].primary_key is True

    def test_id_is_uuid(self):
        assert isinstance(self._cols()["id"].type, PG_UUID)

    # --- user_id ---

    def test_user_id_is_uuid_not_null(self):
        col = self._cols()["user_id"]
        assert isinstance(col.type, PG_UUID)
        assert col.nullable is False

    def test_user_id_is_unique(self):
        assert self._cols()["user_id"].unique is True

    def test_user_id_is_indexed(self):
        assert self._cols()["user_id"].index is True

    def test_user_id_fk_points_to_users(self):
        fk_targets = {fk.target_fullname for fk in self._cols()["user_id"].foreign_keys}
        assert "users.id" in fk_targets

    def test_user_id_fk_ondelete_restrict(self):
        fks = list(self._cols()["user_id"].foreign_keys)
        assert len(fks) == 1
        assert fks[0].ondelete.upper() == "RESTRICT"

    # --- optional profile fields ---

    def test_phone_is_varchar20_nullable(self):
        col = self._cols()["phone"]
        assert isinstance(col.type, String)
        assert col.type.length == 20
        assert col.nullable is True

    def test_date_of_birth_is_date_nullable(self):
        col = self._cols()["date_of_birth"]
        assert isinstance(col.type, Date)
        assert col.nullable is True

    def test_bio_is_text_nullable(self):
        col = self._cols()["bio"]
        assert isinstance(col.type, Text)
        assert col.nullable is True

    def test_resume_content_is_text_nullable(self):
        col = self._cols()["resume_content"]
        assert isinstance(col.type, Text)
        assert col.nullable is True

    # --- eligibility fields ---

    def test_current_gpa_is_numeric_nullable(self):
        col = self._cols()["current_gpa"]
        assert isinstance(col.type, Numeric)
        assert col.nullable is True

    def test_current_gpa_precision_scale(self):
        col = self._cols()["current_gpa"]
        assert col.type.precision == 4
        assert col.type.scale == 2

    def test_graduation_year_is_integer_nullable(self):
        col = self._cols()["graduation_year"]
        assert isinstance(col.type, Integer)
        assert col.nullable is True

    # --- timestamps ---

    def test_timestamps_are_timezone_aware(self):
        cols = self._cols()
        for name in ("created_at", "updated_at"):
            assert isinstance(cols[name].type, DateTime)
            assert cols[name].type.timezone is True

    # --- check constraint ---

    def test_gpa_check_constraint_exists(self):
        names = {c.name for c in StudentProfile.__table__.constraints}
        assert "ck_student_profiles_current_gpa" in names


class TestStudentProfileInstantiation:

    def test_minimal_instantiation(self):
        sp = StudentProfile(user_id=uuid.uuid4())
        assert sp.user_id is not None

    def test_optional_fields_are_none_by_default(self):
        sp = StudentProfile(user_id=uuid.uuid4())
        assert sp.phone is None
        assert sp.date_of_birth is None
        assert sp.bio is None
        assert sp.resume_content is None
        assert sp.current_gpa is None
        assert sp.graduation_year is None

    def test_can_set_all_fields(self):
        uid = uuid.uuid4()
        sp = StudentProfile(
            user_id=uid,
            phone="9876543210",
            bio="Computer Science student",
            resume_content="# Resume",
            current_gpa=Decimal("8.75"),
            graduation_year=2025,
        )
        assert sp.phone == "9876543210"
        assert sp.current_gpa == Decimal("8.75")
        assert sp.graduation_year == 2025

    def test_repr_contains_user_id(self):
        uid = uuid.uuid4()
        sp = StudentProfile(user_id=uid)
        assert str(uid) in repr(sp)


class TestStudentProfileDiscoverability:

    def test_importable_from_models_package(self):
        from app.models import StudentProfile as SP
        assert SP is StudentProfile

    def test_in_base_metadata(self):
        assert "student_profiles" in Base.metadata.tables
