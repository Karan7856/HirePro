"""Tests for database configuration — no live PostgreSQL connection required."""
from sqlalchemy import Engine


def test_database_url_format():
    """DATABASE_URL should use the postgresql+psycopg scheme."""
    from app.core.config import settings

    url = settings.DATABASE_URL
    assert url.startswith("postgresql+psycopg://")


def test_database_url_contains_credentials():
    """DATABASE_URL should embed user, password, host, port, and db name."""
    from app.core.config import Settings

    s = Settings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpass",
        POSTGRES_HOST="testhost",
        POSTGRES_PORT=5433,
        POSTGRES_DB="testdb",
    )
    assert s.DATABASE_URL == "postgresql+psycopg://testuser:testpass@testhost:5433/testdb"


def test_engine_is_sqlalchemy_engine():
    """engine in database.py should be a SQLAlchemy Engine instance."""
    from app.db.database import engine

    assert isinstance(engine, Engine)


def test_engine_uses_correct_url():
    """Engine should be created with the URL from settings."""
    from app.core.config import settings
    from app.db.database import engine

    assert str(engine.url).startswith("postgresql+psycopg://")
    assert settings.POSTGRES_HOST in str(engine.url)
    assert settings.POSTGRES_DB in str(engine.url)
