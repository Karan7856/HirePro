"""Unit tests for the RecruiterProfile ORM model — no database connection required."""
import uuid

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base
from app.models.recruiter_profile import RecruiterProfile


class TestRecruiterProfileMetadata:

    def _cols(self) -> dict:
        return {c.name: c for c in RecruiterProfile.__table__.columns}

    def test_table_name(self):
        assert RecruiterProfile.__tablename__ == "recruiter_profiles"

    def test_registered_in_base_metadata(self):
        assert "recruiter_profiles" in Base.metadata.tables

    def test_required_columns_exist(self):
        expected = {
            "id", "user_id", "phone", "designation",
            "company_id", "created_at", "updated_at",
        }
        assert set(self._cols().keys()) == expected

    def test_no_extra_columns(self):
        assert len(self._cols()) == 7

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

    # --- company_id ---

    def test_company_id_is_uuid_nullable(self):
        col = self._cols()["company_id"]
        assert isinstance(col.type, PG_UUID)
        assert col.nullable is True

    def test_company_id_is_indexed(self):
        assert self._cols()["company_id"].index is True

    def test_company_id_fk_points_to_companies(self):
        fk_targets = {fk.target_fullname for fk in self._cols()["company_id"].foreign_keys}
        assert "companies.id" in fk_targets

    def test_company_id_fk_ondelete_set_null(self):
        fks = list(self._cols()["company_id"].foreign_keys)
        assert len(fks) == 1
        assert fks[0].ondelete.upper() == "SET NULL"

    # --- optional profile fields ---

    def test_phone_is_varchar20_nullable(self):
        col = self._cols()["phone"]
        assert isinstance(col.type, String)
        assert col.type.length == 20
        assert col.nullable is True

    def test_designation_is_varchar100_nullable(self):
        col = self._cols()["designation"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is True

    # --- timestamps ---

    def test_timestamps_are_timezone_aware(self):
        cols = self._cols()
        for name in ("created_at", "updated_at"):
            assert isinstance(cols[name].type, DateTime)
            assert cols[name].type.timezone is True

    # --- no check constraints expected ---

    def test_no_spurious_check_constraints(self):
        # RecruiterProfile has no CHECK constraints in the architecture.
        from sqlalchemy import CheckConstraint
        check_constraints = [
            c for c in RecruiterProfile.__table__.constraints
            if isinstance(c, CheckConstraint)
        ]
        assert len(check_constraints) == 0


class TestRecruiterProfileInstantiation:

    def test_minimal_instantiation(self):
        rp = RecruiterProfile(user_id=uuid.uuid4())
        assert rp.user_id is not None

    def test_optional_fields_are_none_by_default(self):
        rp = RecruiterProfile(user_id=uuid.uuid4())
        assert rp.phone is None
        assert rp.designation is None
        assert rp.company_id is None

    def test_company_id_can_be_set(self):
        uid = uuid.uuid4()
        cid = uuid.uuid4()
        rp = RecruiterProfile(user_id=uid, company_id=cid, designation="Engineering Lead")
        assert rp.company_id == cid
        assert rp.designation == "Engineering Lead"

    def test_repr_contains_user_id(self):
        uid = uuid.uuid4()
        rp = RecruiterProfile(user_id=uid)
        assert str(uid) in repr(rp)

    def test_repr_contains_company_id(self):
        uid = uuid.uuid4()
        cid = uuid.uuid4()
        rp = RecruiterProfile(user_id=uid, company_id=cid)
        assert str(cid) in repr(rp)


class TestRecruiterProfileDiscoverability:

    def test_importable_from_models_package(self):
        from app.models import RecruiterProfile as RP
        assert RP is RecruiterProfile

    def test_all_four_models_in_metadata(self):
        tables = Base.metadata.tables
        for table in ("users", "companies", "student_profiles", "recruiter_profiles"):
            assert table in tables
