"""Unit tests for the JobSkill junction table — no database connection required."""
import uuid

from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base
from app.models.job_skill import JobSkill


class TestJobSkillMetadata:

    def _cols(self) -> dict:
        return {c.name: c for c in JobSkill.__table__.columns}

    def test_table_name(self):
        assert JobSkill.__tablename__ == "job_skills"

    def test_registered_in_base_metadata(self):
        assert "job_skills" in Base.metadata.tables

    def test_required_columns_exist(self):
        assert set(self._cols().keys()) == {"job_id", "skill_id"}

    def test_no_extra_columns(self):
        assert len(self._cols()) == 2

    def test_no_separate_id_column(self):
        assert "id" not in self._cols()

    # --- job_id ---

    def test_job_id_is_uuid(self):
        assert isinstance(self._cols()["job_id"].type, PG_UUID)

    def test_job_id_is_not_null(self):
        assert self._cols()["job_id"].nullable is False

    def test_job_id_fk_points_to_jobs(self):
        fk_targets = {
            fk.target_fullname
            for fk in self._cols()["job_id"].foreign_keys
        }
        assert "jobs.id" in fk_targets

    def test_job_id_fk_ondelete_cascade(self):
        fks = list(self._cols()["job_id"].foreign_keys)
        assert len(fks) == 1
        assert fks[0].ondelete.upper() == "CASCADE"

    # --- skill_id ---

    def test_skill_id_is_uuid(self):
        assert isinstance(self._cols()["skill_id"].type, PG_UUID)

    def test_skill_id_is_not_null(self):
        assert self._cols()["skill_id"].nullable is False

    def test_skill_id_fk_points_to_skills(self):
        fk_targets = {
            fk.target_fullname
            for fk in self._cols()["skill_id"].foreign_keys
        }
        assert "skills.id" in fk_targets

    def test_skill_id_fk_ondelete_restrict(self):
        fks = list(self._cols()["skill_id"].foreign_keys)
        assert len(fks) == 1
        assert fks[0].ondelete.upper() == "RESTRICT"

    # --- composite primary key ---

    def test_composite_pk_exists(self):
        pk_constraints = [
            c for c in JobSkill.__table__.constraints
            if isinstance(c, PrimaryKeyConstraint)
        ]
        assert len(pk_constraints) == 1

    def test_composite_pk_covers_both_columns(self):
        pk = next(
            c for c in JobSkill.__table__.constraints
            if isinstance(c, PrimaryKeyConstraint)
        )
        col_names = {col.name for col in pk.columns}
        assert col_names == {"job_id", "skill_id"}

    def test_both_columns_are_primary_key_members(self):
        cols = self._cols()
        assert cols["job_id"].primary_key is True
        assert cols["skill_id"].primary_key is True


class TestJobSkillInstantiation:

    def _make(self, **kwargs) -> JobSkill:
        defaults = dict(
            job_id=uuid.uuid4(),
            skill_id=uuid.uuid4(),
        )
        defaults.update(kwargs)
        return JobSkill(**defaults)

    def test_minimal_instantiation(self):
        js = self._make()
        assert js.job_id is not None
        assert js.skill_id is not None

    def test_can_set_specific_ids(self):
        j_id = uuid.uuid4()
        sk_id = uuid.uuid4()
        js = self._make(job_id=j_id, skill_id=sk_id)
        assert js.job_id == j_id
        assert js.skill_id == sk_id

    def test_repr_contains_both_ids(self):
        j_id = uuid.uuid4()
        sk_id = uuid.uuid4()
        js = self._make(job_id=j_id, skill_id=sk_id)
        r = repr(js)
        assert str(j_id) in r
        assert str(sk_id) in r

    def test_different_jobs_same_skill(self):
        sk_id = uuid.uuid4()
        js1 = self._make(job_id=uuid.uuid4(), skill_id=sk_id)
        js2 = self._make(job_id=uuid.uuid4(), skill_id=sk_id)
        assert js1.skill_id == js2.skill_id
        assert js1.job_id != js2.job_id

    def test_same_job_different_skills(self):
        j_id = uuid.uuid4()
        js1 = self._make(job_id=j_id, skill_id=uuid.uuid4())
        js2 = self._make(job_id=j_id, skill_id=uuid.uuid4())
        assert js1.job_id == js2.job_id
        assert js1.skill_id != js2.skill_id


class TestJobSkillDiscoverability:

    def test_importable_from_models_package(self):
        from app.models import JobSkill as ImportedJS
        assert ImportedJS is JobSkill

    def test_job_skills_table_in_base_metadata(self):
        assert "job_skills" in Base.metadata.tables

    def test_all_model_tables_in_metadata(self):
        tables = Base.metadata.tables
        for t in (
            "users", "companies", "student_profiles", "recruiter_profiles",
            "jobs", "applications", "application_status_history",
            "education", "skills", "student_skills", "job_skills",
        ):
            assert t in tables
