"""Unit tests for the Skill ORM model — no database connection required."""
import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base
from app.models.skill import Skill


class TestSkillModelMetadata:

    def _cols(self) -> dict:
        return {c.name: c for c in Skill.__table__.columns}

    def test_table_name(self):
        assert Skill.__tablename__ == "skills"

    def test_registered_in_base_metadata(self):
        assert "skills" in Base.metadata.tables

    def test_required_columns_exist(self):
        assert set(self._cols().keys()) == {"id", "name"}

    def test_no_extra_columns(self):
        assert len(self._cols()) == 2

    # --- primary key ---

    def test_primary_key_is_id(self):
        assert self._cols()["id"].primary_key is True

    def test_id_is_uuid(self):
        assert isinstance(self._cols()["id"].type, PG_UUID)

    def test_id_is_not_null(self):
        assert self._cols()["id"].nullable is False

    # --- name ---

    def test_name_is_varchar100(self):
        col = self._cols()["name"]
        assert isinstance(col.type, String)
        assert col.type.length == 100

    def test_name_is_not_null(self):
        assert self._cols()["name"].nullable is False

    def test_name_is_unique(self):
        assert self._cols()["name"].unique is True

    def test_name_is_indexed(self):
        assert self._cols()["name"].index is True


class TestSkillInstantiation:

    def test_minimal_instantiation(self):
        skill = Skill(name="python")
        assert skill.name == "python"

    def test_id_default_is_uuid(self):
        # SQLAlchemy 2.x column defaults fire at INSERT, not on bare
        # instantiation. Verify a default is registered and it produces a UUID.
        col = Skill.__table__.columns["id"]
        assert col.default is not None
        # The default callable is wrapped by SQLAlchemy; call via execute(None).
        result = col.default.arg(None)
        assert isinstance(result, uuid.UUID)

    def test_two_skills_get_distinct_ids(self):
        col = Skill.__table__.columns["id"]
        id1 = col.default.arg(None)
        id2 = col.default.arg(None)
        assert isinstance(id1, uuid.UUID)
        assert id1 != id2

    def test_can_set_various_skill_names(self):
        for name in ("python", "java", "react", "sql", "machine-learning"):
            skill = Skill(name=name)
            assert skill.name == name

    def test_repr_contains_name(self):
        skill = Skill(name="fastapi")
        assert "fastapi" in repr(skill)

    def test_repr_contains_id(self):
        skill = Skill(name="fastapi")
        assert str(skill.id) in repr(skill)


class TestSkillDiscoverability:

    def test_importable_from_models_package(self):
        from app.models import Skill as ImportedSkill
        assert ImportedSkill is Skill

    def test_skills_table_in_base_metadata(self):
        assert "skills" in Base.metadata.tables

    def test_all_model_tables_in_metadata(self):
        tables = Base.metadata.tables
        for t in (
            "users", "companies", "student_profiles", "recruiter_profiles",
            "jobs", "applications", "application_status_history",
            "education", "skills",
        ):
            assert t in tables
