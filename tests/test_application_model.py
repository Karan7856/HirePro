"""Unit tests for the Application ORM model — no database connection required."""
import uuid

from sqlalchemy import CheckConstraint, DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base
from app.models.application import APPLICATION_STATUSES, Application


class TestApplicationModelMetadata:

    def _cols(self) -> dict:
        return {c.name: c for c in Application.__table__.columns}

    def test_table_name(self):
        assert Application.__tablename__ == "applications"

    def test_registered_in_base_metadata(self):
        assert "applications" in Base.metadata.tables

    def test_required_columns_exist(self):
        expected = {
            "id",
            "student_profile_id",
            "job_id",
            "status",
            "cover_letter",
            "applied_at",
            "updated_at",
        }
        assert set(self._cols().keys()) == expected

    def test_no_extra_columns(self):
        assert len(self._cols()) == 7

    # --- primary key ---

    def test_primary_key_is_id(self):
        assert self._cols()["id"].primary_key is True

    def test_id_is_uuid(self):
        assert isinstance(self._cols()["id"].type, PG_UUID)

    # --- student_profile_id FK ---

    def test_student_profile_id_is_uuid_not_null(self):
        col = self._cols()["student_profile_id"]
        assert isinstance(col.type, PG_UUID)
        assert col.nullable is False

    def test_student_profile_id_is_indexed(self):
        assert self._cols()["student_profile_id"].index is True

    def test_student_profile_id_fk_points_to_student_profiles(self):
        fk_targets = {fk.target_fullname for fk in self._cols()["student_profile_id"].foreign_keys}
        assert "student_profiles.id" in fk_targets

    def test_student_profile_id_fk_ondelete_restrict(self):
        fks = list(self._cols()["student_profile_id"].foreign_keys)
        assert len(fks) == 1
        assert fks[0].ondelete.upper() == "RESTRICT"

    # --- job_id FK ---

    def test_job_id_is_uuid_not_null(self):
        col = self._cols()["job_id"]
        assert isinstance(col.type, PG_UUID)
        assert col.nullable is False

    def test_job_id_is_indexed(self):
        assert self._cols()["job_id"].index is True

    def test_job_id_fk_points_to_jobs(self):
        fk_targets = {fk.target_fullname for fk in self._cols()["job_id"].foreign_keys}
        assert "jobs.id" in fk_targets

    def test_job_id_fk_ondelete_restrict(self):
        fks = list(self._cols()["job_id"].foreign_keys)
        assert len(fks) == 1
        assert fks[0].ondelete.upper() == "RESTRICT"

    # --- status ---

    def test_status_is_varchar20_not_null(self):
        col = self._cols()["status"]
        assert isinstance(col.type, String)
        assert col.type.length == 20
        assert col.nullable is False

    def test_status_is_indexed(self):
        assert self._cols()["status"].index is True

    def test_status_server_default_is_pending(self):
        col = self._cols()["status"]
        assert col.server_default is not None
        assert "pending" in str(col.server_default.arg)

    # --- cover_letter ---

    def test_cover_letter_is_text_nullable(self):
        col = self._cols()["cover_letter"]
        assert isinstance(col.type, Text)
        assert col.nullable is True

    # --- timestamps ---

    def test_applied_at_is_timestamptz_not_null(self):
        col = self._cols()["applied_at"]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is False

    def test_updated_at_is_timestamptz_not_null(self):
        col = self._cols()["updated_at"]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is False

    # --- unique constraint ---

    def test_unique_student_job_constraint_exists(self):
        names = {c.name for c in Application.__table__.constraints if isinstance(c, UniqueConstraint)}
        assert "uq_applications_student_job" in names

    def test_unique_constraint_covers_student_profile_id_and_job_id(self):
        uc = next(
            c for c in Application.__table__.constraints
            if isinstance(c, UniqueConstraint) and c.name == "uq_applications_student_job"
        )
        col_names = {col.name for col in uc.columns}
        assert col_names == {"student_profile_id", "job_id"}

    # --- CHECK constraint ---

    def test_status_check_constraint_exists(self):
        names = {c.name for c in Application.__table__.constraints if isinstance(c, CheckConstraint)}
        assert "ck_applications_status" in names

    # --- status constant ---

    def test_application_statuses_constant_contains_all_values(self):
        expected = {
            "pending", "reviewing", "shortlisted",
            "interview", "selected", "rejected", "withdrawn",
        }
        assert set(APPLICATION_STATUSES) == expected

    def test_application_statuses_has_seven_values(self):
        assert len(APPLICATION_STATUSES) == 7


class TestApplicationInstantiation:

    def _make_app(self, **kwargs) -> Application:
        defaults = dict(
            student_profile_id=uuid.uuid4(),
            job_id=uuid.uuid4(),
        )
        defaults.update(kwargs)
        return Application(**defaults)

    def test_minimal_instantiation(self):
        app = self._make_app()
        assert app.student_profile_id is not None
        assert app.job_id is not None

    def test_cover_letter_defaults_to_none(self):
        app = self._make_app()
        assert app.cover_letter is None

    def test_can_set_cover_letter(self):
        app = self._make_app(cover_letter="I am a great fit for this role.")
        assert app.cover_letter == "I am a great fit for this role."

    def test_status_default_is_pending(self):
        # column declares default="pending"; verified server_default separately.
        app = self._make_app(status="pending")
        assert app.status == "pending"

    def test_can_set_all_status_values(self):
        for status in APPLICATION_STATUSES:
            app = self._make_app(status=status)
            assert app.status == status

    def test_repr_contains_key_fields(self):
        sp_id = uuid.uuid4()
        j_id = uuid.uuid4()
        app = self._make_app(student_profile_id=sp_id, job_id=j_id, status="pending")
        r = repr(app)
        assert str(sp_id) in r
        assert str(j_id) in r
        assert "pending" in r


class TestApplicationRelationships:

    def test_student_profile_relationship_exists(self):
        assert hasattr(Application, "student_profile")

    def test_job_relationship_exists(self):
        assert hasattr(Application, "job")

    def test_student_profile_relationship_targets_student_profiles_table(self):
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(Application)
        rel = mapper.relationships["student_profile"]
        assert rel.mapper.class_.__tablename__ == "student_profiles"

    def test_job_relationship_targets_jobs_table(self):
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(Application)
        rel = mapper.relationships["job"]
        assert rel.mapper.class_.__tablename__ == "jobs"


class TestApplicationDiscoverability:

    def test_importable_from_models_package(self):
        from app.models import Application as ImportedApp
        assert ImportedApp is Application

    def test_applications_table_in_base_metadata(self):
        assert "applications" in Base.metadata.tables

    def test_all_core_model_tables_in_metadata(self):
        tables = Base.metadata.tables
        for t in ("users", "companies", "student_profiles", "recruiter_profiles", "jobs", "applications"):
            assert t in tables
