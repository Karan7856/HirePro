"""Unit tests for the StudentSkill junction table — no database connection required."""
import uuid

from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base
from app.models.student_skill import StudentSkill


class TestStudentSkillMetadata:

    def _cols(self) -> dict:
        return {c.name: c for c in StudentSkill.__table__.columns}

    def test_table_name(self):
        assert StudentSkill.__tablename__ == "student_skills"

    def test_registered_in_base_metadata(self):
        assert "student_skills" in Base.metadata.tables

    def test_required_columns_exist(self):
        assert set(self._cols().keys()) == {"student_profile_id", "skill_id"}

    def test_no_extra_columns(self):
        assert len(self._cols()) == 2

    # --- student_profile_id ---

    def test_student_profile_id_is_uuid(self):
        assert isinstance(self._cols()["student_profile_id"].type, PG_UUID)

    def test_student_profile_id_is_not_null(self):
        assert self._cols()["student_profile_id"].nullable is False

    def test_student_profile_id_fk_points_to_student_profiles(self):
        fk_targets = {
            fk.target_fullname
            for fk in self._cols()["student_profile_id"].foreign_keys
        }
        assert "student_profiles.id" in fk_targets

    def test_student_profile_id_fk_ondelete_cascade(self):
        fks = list(self._cols()["student_profile_id"].foreign_keys)
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

    # --- primary key / composite PK ---

    def test_composite_pk_exists(self):
        pk_constraints = [
            c for c in StudentSkill.__table__.constraints
            if isinstance(c, PrimaryKeyConstraint)
        ]
        assert len(pk_constraints) == 1

    def test_composite_pk_covers_both_columns(self):
        pk = next(
            c for c in StudentSkill.__table__.constraints
            if isinstance(c, PrimaryKeyConstraint)
        )
        col_names = {col.name for col in pk.columns}
        assert col_names == {"student_profile_id", "skill_id"}

    def test_both_columns_are_primary_key_members(self):
        cols = self._cols()
        assert cols["student_profile_id"].primary_key is True
        assert cols["skill_id"].primary_key is True

    def test_no_separate_id_column(self):
        assert "id" not in self._cols()


class TestStudentSkillInstantiation:

    def _make(self, **kwargs) -> StudentSkill:
        defaults = dict(
            student_profile_id=uuid.uuid4(),
            skill_id=uuid.uuid4(),
        )
        defaults.update(kwargs)
        return StudentSkill(**defaults)

    def test_minimal_instantiation(self):
        ss = self._make()
        assert ss.student_profile_id is not None
        assert ss.skill_id is not None

    def test_can_set_specific_ids(self):
        sp_id = uuid.uuid4()
        sk_id = uuid.uuid4()
        ss = self._make(student_profile_id=sp_id, skill_id=sk_id)
        assert ss.student_profile_id == sp_id
        assert ss.skill_id == sk_id

    def test_repr_contains_both_ids(self):
        sp_id = uuid.uuid4()
        sk_id = uuid.uuid4()
        ss = self._make(student_profile_id=sp_id, skill_id=sk_id)
        r = repr(ss)
        assert str(sp_id) in r
        assert str(sk_id) in r

    def test_different_students_same_skill(self):
        sk_id = uuid.uuid4()
        ss1 = self._make(student_profile_id=uuid.uuid4(), skill_id=sk_id)
        ss2 = self._make(student_profile_id=uuid.uuid4(), skill_id=sk_id)
        assert ss1.skill_id == ss2.skill_id
        assert ss1.student_profile_id != ss2.student_profile_id

    def test_same_student_different_skills(self):
        sp_id = uuid.uuid4()
        ss1 = self._make(student_profile_id=sp_id, skill_id=uuid.uuid4())
        ss2 = self._make(student_profile_id=sp_id, skill_id=uuid.uuid4())
        assert ss1.student_profile_id == ss2.student_profile_id
        assert ss1.skill_id != ss2.skill_id


class TestStudentSkillDiscoverability:

    def test_importable_from_models_package(self):
        from app.models import StudentSkill as ImportedSS
        assert ImportedSS is StudentSkill

    def test_student_skills_table_in_base_metadata(self):
        assert "student_skills" in Base.metadata.tables

    def test_all_model_tables_in_metadata(self):
        tables = Base.metadata.tables
        for t in (
            "users", "companies", "student_profiles", "recruiter_profiles",
            "jobs", "applications", "application_status_history",
            "education", "skills", "student_skills",
        ):
            assert t in tables
