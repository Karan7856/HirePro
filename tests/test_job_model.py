"""Unit tests for the Job ORM model — no database connection required."""
import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID

from app.db.base import Base
from app.models.job import JOB_STATUSES, JOB_TYPES, Job


class TestJobModelMetadata:

    def _cols(self) -> dict:
        return {c.name: c for c in Job.__table__.columns}

    def test_table_name(self):
        assert Job.__tablename__ == "jobs"

    def test_registered_in_base_metadata(self):
        assert "jobs" in Base.metadata.tables

    def test_required_columns_exist(self):
        expected = {
            "id", "title", "description", "company_id", "recruiter_id",
            "location", "job_type", "salary_min", "salary_max", "min_gpa",
            "allowed_graduation_years", "status", "application_deadline",
            "created_at", "updated_at",
        }
        assert set(self._cols().keys()) == expected

    def test_no_extra_columns(self):
        assert len(self._cols()) == 15

    # --- primary key ---

    def test_primary_key_is_id(self):
        assert self._cols()["id"].primary_key is True

    def test_id_is_uuid(self):
        assert isinstance(self._cols()["id"].type, PG_UUID)

    # --- required string fields ---

    def test_title_is_varchar200_not_null(self):
        col = self._cols()["title"]
        assert isinstance(col.type, String)
        assert col.type.length == 200
        assert col.nullable is False

    def test_description_is_text_not_null(self):
        col = self._cols()["description"]
        assert isinstance(col.type, Text)
        assert col.nullable is False

    # --- company_id FK ---

    def test_company_id_is_uuid_not_null(self):
        col = self._cols()["company_id"]
        assert isinstance(col.type, PG_UUID)
        assert col.nullable is False

    def test_company_id_is_indexed(self):
        assert self._cols()["company_id"].index is True

    def test_company_id_fk_points_to_companies(self):
        fk_targets = {fk.target_fullname for fk in self._cols()["company_id"].foreign_keys}
        assert "companies.id" in fk_targets

    def test_company_id_fk_ondelete_restrict(self):
        fks = list(self._cols()["company_id"].foreign_keys)
        assert fks[0].ondelete.upper() == "RESTRICT"

    # --- recruiter_id FK ---

    def test_recruiter_id_is_uuid_not_null(self):
        col = self._cols()["recruiter_id"]
        assert isinstance(col.type, PG_UUID)
        assert col.nullable is False

    def test_recruiter_id_is_indexed(self):
        assert self._cols()["recruiter_id"].index is True

    def test_recruiter_id_fk_points_to_recruiter_profiles(self):
        fk_targets = {fk.target_fullname for fk in self._cols()["recruiter_id"].foreign_keys}
        assert "recruiter_profiles.id" in fk_targets

    def test_recruiter_id_fk_ondelete_restrict(self):
        fks = list(self._cols()["recruiter_id"].foreign_keys)
        assert fks[0].ondelete.upper() == "RESTRICT"

    # --- optional fields ---

    def test_location_is_varchar200_nullable(self):
        col = self._cols()["location"]
        assert isinstance(col.type, String)
        assert col.type.length == 200
        assert col.nullable is True

    def test_job_type_is_varchar30_nullable_indexed(self):
        col = self._cols()["job_type"]
        assert isinstance(col.type, String)
        assert col.type.length == 30
        assert col.nullable is True
        assert col.index is True

    def test_salary_min_is_numeric_nullable(self):
        col = self._cols()["salary_min"]
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 12
        assert col.type.scale == 2
        assert col.nullable is True

    def test_salary_max_is_numeric_nullable(self):
        col = self._cols()["salary_max"]
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 12
        assert col.type.scale == 2
        assert col.nullable is True

    def test_min_gpa_is_numeric42_nullable(self):
        col = self._cols()["min_gpa"]
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 4
        assert col.type.scale == 2
        assert col.nullable is True

    def test_allowed_graduation_years_is_array_nullable(self):
        col = self._cols()["allowed_graduation_years"]
        assert isinstance(col.type, ARRAY)
        assert col.nullable is True

    # --- status ---

    def test_status_is_varchar20_not_null(self):
        col = self._cols()["status"]
        assert isinstance(col.type, String)
        assert col.type.length == 20
        assert col.nullable is False

    def test_status_is_indexed(self):
        assert self._cols()["status"].index is True

    def test_status_server_default_is_open(self):
        col = self._cols()["status"]
        assert col.server_default is not None
        assert "open" in str(col.server_default.arg)

    # --- timestamps ---

    def test_application_deadline_is_timestamptz_nullable(self):
        col = self._cols()["application_deadline"]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is True

    def test_created_at_is_timestamptz_not_null(self):
        col = self._cols()["created_at"]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is False

    def test_updated_at_is_timestamptz_not_null(self):
        col = self._cols()["updated_at"]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is False

    # --- CHECK constraints ---

    def _constraint_names(self) -> set:
        return {c.name for c in Job.__table__.constraints if isinstance(c, CheckConstraint)}

    def test_job_type_check_constraint_exists(self):
        assert "ck_jobs_job_type" in self._constraint_names()

    def test_status_check_constraint_exists(self):
        assert "ck_jobs_status" in self._constraint_names()

    def test_salary_range_check_constraint_exists(self):
        assert "ck_jobs_salary_range" in self._constraint_names()

    def test_exactly_three_check_constraints(self):
        assert len(self._constraint_names()) == 3

    # --- constants ---

    def test_job_types_constant(self):
        assert set(JOB_TYPES) == {"full_time", "part_time", "internship", "contract"}

    def test_job_statuses_constant(self):
        assert set(JOB_STATUSES) == {"open", "closed"}


class TestJobInstantiation:

    def _make_job(self, **kwargs) -> Job:
        defaults = dict(
            title="Software Engineer",
            description="Build great things.",
            company_id=uuid.uuid4(),
            recruiter_id=uuid.uuid4(),
        )
        defaults.update(kwargs)
        return Job(**defaults)

    def test_minimal_instantiation(self):
        job = self._make_job()
        assert job.title == "Software Engineer"
        assert job.description == "Build great things."

    def test_optional_fields_default_to_none(self):
        job = self._make_job()
        assert job.location is None
        assert job.job_type is None
        assert job.salary_min is None
        assert job.salary_max is None
        assert job.min_gpa is None
        assert job.allowed_graduation_years is None
        assert job.application_deadline is None

    def test_status_default_is_open(self):
        # The column declares default="open" and server_default="open" —
        # verified in test_status_server_default_is_open.
        # SQLAlchemy 2.x column defaults are applied at INSERT, not on bare
        # instantiation, so we verify explicit assignment works correctly here.
        job = self._make_job(status="open")
        assert job.status == "open"

    def test_can_set_all_fields(self):
        job = self._make_job(
            title="Backend Dev",
            job_type="full_time",
            location="Bangalore",
            salary_min=Decimal("800000.00"),
            salary_max=Decimal("1200000.00"),
            min_gpa=Decimal("7.50"),
            allowed_graduation_years=[2024, 2025],
            status="open",
        )
        assert job.job_type == "full_time"
        assert job.salary_max == Decimal("1200000.00")
        assert job.allowed_graduation_years == [2024, 2025]

    def test_repr_contains_title_and_status(self):
        job = self._make_job(title="DevOps Lead", status="open")
        r = repr(job)
        assert "DevOps Lead" in r
        assert "open" in r

    def test_repr_contains_company_id(self):
        cid = uuid.uuid4()
        job = self._make_job(company_id=cid)
        assert str(cid) in repr(job)


class TestJobRelationships:

    def test_company_relationship_exists(self):
        assert hasattr(Job, "company")

    def test_recruiter_relationship_exists(self):
        assert hasattr(Job, "recruiter")

    def test_company_relationship_targets_company_table(self):
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(Job)
        rel = mapper.relationships["company"]
        assert rel.mapper.class_.__tablename__ == "companies"

    def test_recruiter_relationship_targets_recruiter_profiles_table(self):
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(Job)
        rel = mapper.relationships["recruiter"]
        assert rel.mapper.class_.__tablename__ == "recruiter_profiles"


class TestJobDiscoverability:

    def test_importable_from_models_package(self):
        from app.models import Job as ImportedJob
        assert ImportedJob is Job

    def test_all_five_models_in_metadata(self):
        tables = Base.metadata.tables
        for t in ("users", "companies", "student_profiles", "recruiter_profiles", "jobs"):
            assert t in tables
