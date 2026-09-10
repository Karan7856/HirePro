"""Unit tests for the Education ORM model — no database connection required."""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base
from app.models.education import Education


class TestEducationModelMetadata:

    def _cols(self) -> dict:
        return {c.name: c for c in Education.__table__.columns}

    def test_table_name(self):
        assert Education.__tablename__ == "education"

    def test_registered_in_base_metadata(self):
        assert "education" in Base.metadata.tables

    def test_required_columns_exist(self):
        expected = {
            "id",
            "student_profile_id",
            "institution",
            "degree",
            "field_of_study",
            "start_date",
            "end_date",
            "gpa",
            "created_at",
            "updated_at",
        }
        assert set(self._cols().keys()) == expected

    def test_no_extra_columns(self):
        assert len(self._cols()) == 10

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

    def test_student_profile_id_fk_ondelete_cascade(self):
        fks = list(self._cols()["student_profile_id"].foreign_keys)
        assert len(fks) == 1
        assert fks[0].ondelete.upper() == "CASCADE"

    # --- institution ---

    def test_institution_is_varchar200_not_null(self):
        col = self._cols()["institution"]
        assert isinstance(col.type, String)
        assert col.type.length == 200
        assert col.nullable is False

    # --- degree ---

    def test_degree_is_varchar100_not_null(self):
        col = self._cols()["degree"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is False

    # --- field_of_study ---

    def test_field_of_study_is_varchar150_nullable(self):
        col = self._cols()["field_of_study"]
        assert isinstance(col.type, String)
        assert col.type.length == 150
        assert col.nullable is True

    # --- dates ---

    def test_start_date_is_date_nullable(self):
        col = self._cols()["start_date"]
        assert isinstance(col.type, Date)
        assert col.nullable is True

    def test_end_date_is_date_nullable(self):
        col = self._cols()["end_date"]
        assert isinstance(col.type, Date)
        assert col.nullable is True

    # --- gpa ---

    def test_gpa_is_numeric42_nullable(self):
        col = self._cols()["gpa"]
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 4
        assert col.type.scale == 2
        assert col.nullable is True

    # --- timestamps ---

    def test_created_at_is_timestamptz_not_null(self):
        col = self._cols()["created_at"]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is False

    def test_created_at_has_server_default(self):
        assert self._cols()["created_at"].server_default is not None

    def test_updated_at_is_timestamptz_not_null(self):
        col = self._cols()["updated_at"]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is False

    def test_updated_at_has_server_default(self):
        assert self._cols()["updated_at"].server_default is not None

    # --- CHECK constraint ---

    def test_gpa_check_constraint_exists(self):
        names = {c.name for c in Education.__table__.constraints if isinstance(c, CheckConstraint)}
        assert "ck_education_gpa" in names

    def test_exactly_one_check_constraint(self):
        check_constraints = [c for c in Education.__table__.constraints if isinstance(c, CheckConstraint)]
        assert len(check_constraints) == 1

    # --- indexes ---

    def test_student_profile_id_column_index_exists(self):
        assert self._cols()["student_profile_id"].index is True


class TestEducationInstantiation:

    def _make_education(self, **kwargs) -> Education:
        defaults = dict(
            student_profile_id=uuid.uuid4(),
            institution="IIT Bombay",
            degree="B.Tech",
        )
        defaults.update(kwargs)
        return Education(**defaults)

    def test_minimal_instantiation(self):
        edu = self._make_education()
        assert edu.institution == "IIT Bombay"
        assert edu.degree == "B.Tech"
        assert edu.student_profile_id is not None

    def test_optional_fields_default_to_none(self):
        edu = self._make_education()
        assert edu.field_of_study is None
        assert edu.start_date is None
        assert edu.end_date is None
        assert edu.gpa is None

    def test_end_date_none_means_currently_pursuing(self):
        edu = self._make_education(start_date=date(2020, 7, 1), end_date=None)
        assert edu.end_date is None

    def test_can_set_all_fields(self):
        edu = self._make_education(
            institution="NIT Trichy",
            degree="M.Sc",
            field_of_study="Computer Science",
            start_date=date(2019, 8, 1),
            end_date=date(2023, 5, 31),
            gpa=Decimal("8.75"),
        )
        assert edu.field_of_study == "Computer Science"
        assert edu.gpa == Decimal("8.75")
        assert edu.end_date == date(2023, 5, 31)

    def test_gpa_boundary_zero(self):
        edu = self._make_education(gpa=Decimal("0.00"))
        assert edu.gpa == Decimal("0.00")

    def test_gpa_boundary_ten(self):
        edu = self._make_education(gpa=Decimal("10.00"))
        assert edu.gpa == Decimal("10.00")

    def test_repr_contains_institution_and_degree(self):
        edu = self._make_education(institution="BITS Pilani", degree="B.E.")
        r = repr(edu)
        assert "BITS Pilani" in r
        assert "B.E." in r

    def test_repr_contains_student_profile_id(self):
        sp_id = uuid.uuid4()
        edu = self._make_education(student_profile_id=sp_id)
        assert str(sp_id) in repr(edu)


class TestEducationRelationships:

    def test_student_profile_relationship_exists(self):
        assert hasattr(Education, "student_profile")

    def test_student_profile_relationship_targets_student_profiles_table(self):
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(Education)
        rel = mapper.relationships["student_profile"]
        assert rel.mapper.class_.__tablename__ == "student_profiles"


class TestEducationDiscoverability:

    def test_importable_from_models_package(self):
        from app.models import Education as ImportedEdu
        assert ImportedEdu is Education

    def test_education_table_in_base_metadata(self):
        assert "education" in Base.metadata.tables

    def test_all_model_tables_in_metadata(self):
        tables = Base.metadata.tables
        for t in (
            "users", "companies", "student_profiles", "recruiter_profiles",
            "jobs", "applications", "application_status_history", "education",
        ):
            assert t in tables
