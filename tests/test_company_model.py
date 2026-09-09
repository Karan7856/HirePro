"""Unit tests for the Company ORM model — no database connection required."""
import uuid

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base
from app.models.company import Company


class TestCompanyModelMetadata:
    """Verify table structure via SQLAlchemy metadata introspection."""

    def _cols(self) -> dict:
        return {c.name: c for c in Company.__table__.columns}

    def test_table_name(self):
        assert Company.__tablename__ == "companies"

    def test_registered_in_base_metadata(self):
        assert "companies" in Base.metadata.tables

    def test_required_columns_exist(self):
        expected = {
            "id", "name", "description", "website", "industry",
            "location", "is_active", "created_by", "created_at", "updated_at",
        }
        assert set(self._cols().keys()) == expected

    def test_no_extra_columns(self):
        assert len(self._cols()) == 10

    def test_primary_key_is_id(self):
        cols = self._cols()
        assert cols["id"].primary_key is True

    def test_id_is_uuid(self):
        cols = self._cols()
        assert isinstance(cols["id"].type, PG_UUID)

    def test_name_constraints(self):
        cols = self._cols()
        assert cols["name"].type.length == 255 or cols["name"].type.length == 200
        assert cols["name"].unique is True
        assert cols["name"].nullable is False

    def test_name_max_length(self):
        assert self._cols()["name"].type.length == 200

    def test_description_is_text_and_nullable(self):
        cols = self._cols()
        assert isinstance(cols["description"].type, Text)
        assert cols["description"].nullable is True

    def test_website_max_length_and_nullable(self):
        cols = self._cols()
        assert isinstance(cols["website"].type, String)
        assert cols["website"].type.length == 500
        assert cols["website"].nullable is True

    def test_industry_max_length_and_nullable(self):
        cols = self._cols()
        assert cols["industry"].type.length == 100
        assert cols["industry"].nullable is True

    def test_location_max_length_and_nullable(self):
        cols = self._cols()
        assert cols["location"].type.length == 200
        assert cols["location"].nullable is True

    def test_is_active_is_boolean_not_null(self):
        cols = self._cols()
        assert isinstance(cols["is_active"].type, Boolean)
        assert cols["is_active"].nullable is False

    def test_is_active_defaults_to_true(self):
        assert self._cols()["is_active"].default.arg is True

    def test_is_active_is_indexed(self):
        assert self._cols()["is_active"].index is True

    def test_created_by_is_uuid_and_nullable(self):
        cols = self._cols()
        assert isinstance(cols["created_by"].type, PG_UUID)
        assert cols["created_by"].nullable is True

    def test_created_by_has_foreign_key_to_users(self):
        cols = self._cols()
        fk_targets = {fk.target_fullname for fk in cols["created_by"].foreign_keys}
        assert "users.id" in fk_targets

    def test_timestamps_are_timezone_aware(self):
        cols = self._cols()
        for col_name in ("created_at", "updated_at"):
            col = cols[col_name]
            assert isinstance(col.type, DateTime)
            assert col.type.timezone is True

    def test_name_index_exists(self):
        # name has unique=True which implies an index
        assert self._cols()["name"].unique is True


class TestCompanyInstantiation:
    """Verify Company objects can be constructed without a DB session."""

    def test_minimal_instantiation(self):
        c = Company(name="Acme Corp")
        assert c.name == "Acme Corp"

    def test_optional_fields_default_to_none(self):
        c = Company(name="Acme Corp")
        assert c.description is None
        assert c.website is None
        assert c.industry is None
        assert c.location is None
        assert c.created_by is None

    def test_is_active_when_set_explicitly(self):
        c = Company(name="Active Co", is_active=True)
        assert c.is_active is True

    def test_can_set_all_fields(self):
        uid = uuid.uuid4()
        c = Company(
            name="TechCorp",
            description="A tech company",
            website="https://techcorp.example.com",
            industry="Technology",
            location="Bangalore",
            is_active=True,
            created_by=uid,
        )
        assert c.name == "TechCorp"
        assert c.website == "https://techcorp.example.com"
        assert c.created_by == uid

    def test_repr_contains_name(self):
        c = Company(name="ReprCo", is_active=True)
        assert "ReprCo" in repr(c)

    def test_repr_contains_active_flag(self):
        c = Company(name="ReprCo", is_active=False)
        assert "False" in repr(c)


class TestCompanyRegisteredInMetadata:
    """Verify Alembic discoverability through app/models/__init__.py."""

    def test_company_importable_from_models_package(self):
        from app.models import Company as ImportedCompany
        assert ImportedCompany is Company

    def test_both_user_and_company_in_metadata(self):
        tables = Base.metadata.tables
        assert "users" in tables
        assert "companies" in tables
