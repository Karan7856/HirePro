"""Unit tests for the ApplicationStatusHistory ORM model — no database connection required."""
import uuid

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base
from app.models.application_status_history import ApplicationStatusHistory


class TestApplicationStatusHistoryMetadata:

    def _cols(self) -> dict:
        return {c.name: c for c in ApplicationStatusHistory.__table__.columns}

    def test_table_name(self):
        assert ApplicationStatusHistory.__tablename__ == "application_status_history"

    def test_registered_in_base_metadata(self):
        assert "application_status_history" in Base.metadata.tables

    def test_required_columns_exist(self):
        expected = {"id", "application_id", "old_status", "new_status", "changed_by", "changed_at"}
        assert set(self._cols().keys()) == expected

    def test_no_extra_columns(self):
        assert len(self._cols()) == 6

    # --- primary key ---

    def test_primary_key_is_id(self):
        assert self._cols()["id"].primary_key is True

    def test_id_is_uuid(self):
        assert isinstance(self._cols()["id"].type, PG_UUID)

    # --- application_id FK ---

    def test_application_id_is_uuid_not_null(self):
        col = self._cols()["application_id"]
        assert isinstance(col.type, PG_UUID)
        assert col.nullable is False

    def test_application_id_is_indexed(self):
        assert self._cols()["application_id"].index is True

    def test_application_id_fk_points_to_applications(self):
        fk_targets = {fk.target_fullname for fk in self._cols()["application_id"].foreign_keys}
        assert "applications.id" in fk_targets

    def test_application_id_fk_ondelete_restrict(self):
        fks = list(self._cols()["application_id"].foreign_keys)
        assert len(fks) == 1
        assert fks[0].ondelete.upper() == "RESTRICT"

    # --- old_status ---

    def test_old_status_is_varchar20(self):
        col = self._cols()["old_status"]
        assert isinstance(col.type, String)
        assert col.type.length == 20

    def test_old_status_is_nullable(self):
        assert self._cols()["old_status"].nullable is True

    # --- new_status ---

    def test_new_status_is_varchar20(self):
        col = self._cols()["new_status"]
        assert isinstance(col.type, String)
        assert col.type.length == 20

    def test_new_status_is_not_null(self):
        assert self._cols()["new_status"].nullable is False

    # --- changed_by FK ---

    def test_changed_by_is_uuid_not_null(self):
        col = self._cols()["changed_by"]
        assert isinstance(col.type, PG_UUID)
        assert col.nullable is False

    def test_changed_by_fk_points_to_users(self):
        fk_targets = {fk.target_fullname for fk in self._cols()["changed_by"].foreign_keys}
        assert "users.id" in fk_targets

    def test_changed_by_fk_ondelete_restrict(self):
        fks = list(self._cols()["changed_by"].foreign_keys)
        assert len(fks) == 1
        assert fks[0].ondelete.upper() == "RESTRICT"

    # --- changed_at ---

    def test_changed_at_is_timestamptz_not_null(self):
        col = self._cols()["changed_at"]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is False

    def test_changed_at_has_server_default(self):
        col = self._cols()["changed_at"]
        assert col.server_default is not None

    # --- indexes ---

    def test_application_id_column_index_exists(self):
        assert self._cols()["application_id"].index is True

    def test_changed_at_desc_index_exists(self):
        index_names = {idx.name for idx in ApplicationStatusHistory.__table__.indexes}
        assert "ix_application_status_history_changed_at" in index_names

    def test_changed_at_index_covers_changed_at_column(self):
        idx = next(
            i for i in ApplicationStatusHistory.__table__.indexes
            if i.name == "ix_application_status_history_changed_at"
        )
        col_names = {col.name for col in idx.columns}
        assert "changed_at" in col_names


class TestApplicationStatusHistoryInstantiation:

    def _make_history(self, **kwargs) -> ApplicationStatusHistory:
        defaults = dict(
            application_id=uuid.uuid4(),
            new_status="reviewing",
            changed_by=uuid.uuid4(),
        )
        defaults.update(kwargs)
        return ApplicationStatusHistory(**defaults)

    def test_minimal_instantiation(self):
        h = self._make_history()
        assert h.application_id is not None
        assert h.new_status == "reviewing"
        assert h.changed_by is not None

    def test_old_status_defaults_to_none(self):
        # Initial pending record has no prior status.
        h = self._make_history()
        assert h.old_status is None

    def test_old_status_none_for_initial_pending_record(self):
        h = self._make_history(new_status="pending", old_status=None)
        assert h.old_status is None
        assert h.new_status == "pending"

    def test_old_status_can_be_set(self):
        h = self._make_history(old_status="pending", new_status="reviewing")
        assert h.old_status == "pending"
        assert h.new_status == "reviewing"

    def test_can_set_all_transition_combinations(self):
        from app.models.application import APPLICATION_STATUSES
        for status in APPLICATION_STATUSES:
            h = self._make_history(new_status=status)
            assert h.new_status == status

    def test_repr_contains_key_fields(self):
        app_id = uuid.uuid4()
        h = self._make_history(
            application_id=app_id,
            old_status="pending",
            new_status="reviewing",
        )
        r = repr(h)
        assert str(app_id) in r
        assert "pending" in r
        assert "reviewing" in r

    def test_references_application_by_id(self):
        app_id = uuid.uuid4()
        h = self._make_history(application_id=app_id)
        assert h.application_id == app_id

    def test_references_user_by_changed_by(self):
        user_id = uuid.uuid4()
        h = self._make_history(changed_by=user_id)
        assert h.changed_by == user_id


class TestApplicationStatusHistoryRelationships:

    def test_application_relationship_exists(self):
        assert hasattr(ApplicationStatusHistory, "application")

    def test_changed_by_user_relationship_exists(self):
        assert hasattr(ApplicationStatusHistory, "changed_by_user")

    def test_application_relationship_targets_applications_table(self):
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(ApplicationStatusHistory)
        rel = mapper.relationships["application"]
        assert rel.mapper.class_.__tablename__ == "applications"

    def test_changed_by_user_relationship_targets_users_table(self):
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(ApplicationStatusHistory)
        rel = mapper.relationships["changed_by_user"]
        assert rel.mapper.class_.__tablename__ == "users"


class TestApplicationStatusHistoryDiscoverability:

    def test_importable_from_models_package(self):
        from app.models import ApplicationStatusHistory as ImportedASH
        assert ImportedASH is ApplicationStatusHistory

    def test_table_in_base_metadata(self):
        assert "application_status_history" in Base.metadata.tables

    def test_all_model_tables_in_metadata(self):
        tables = Base.metadata.tables
        for t in (
            "users", "companies", "student_profiles", "recruiter_profiles",
            "jobs", "applications", "application_status_history",
        ):
            assert t in tables
