"""Tests for SQLAlchemy session factory and get_db dependency.

No live PostgreSQL connection is required — all tests use mocks or
inspect factory behaviour without actually connecting to the database.
"""
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session


def test_session_local_is_callable():
    """SessionLocal should be a callable session factory."""
    from app.db.database import SessionLocal

    assert callable(SessionLocal)


def test_session_local_produces_session():
    """SessionLocal() should return a SQLAlchemy Session instance."""
    with patch("app.db.database.engine") as mock_engine:
        mock_engine.connect.return_value = MagicMock()
        from app.db.database import SessionLocal

        session = SessionLocal()
        try:
            assert isinstance(session, Session)
        finally:
            session.close()


def test_get_db_yields_session():
    """get_db should yield a Session object."""
    with patch("app.db.database.SessionLocal") as mock_factory:
        mock_session = MagicMock(spec=Session)
        mock_factory.return_value = mock_session

        from app.db.database import get_db

        gen = get_db()
        session = next(gen)

        assert session is mock_session


def test_get_db_closes_session_on_exit():
    """get_db should close the session in the finally block."""
    with patch("app.db.database.SessionLocal") as mock_factory:
        mock_session = MagicMock(spec=Session)
        mock_factory.return_value = mock_session

        from app.db.database import get_db

        gen = get_db()
        next(gen)
        try:
            next(gen)
        except StopIteration:
            pass

        mock_session.close.assert_called_once()


def test_get_db_closes_session_on_exception():
    """get_db should close the session even when an exception is raised."""
    with patch("app.db.database.SessionLocal") as mock_factory:
        mock_session = MagicMock(spec=Session)
        mock_factory.return_value = mock_session

        from app.db.database import get_db

        gen = get_db()
        next(gen)
        try:
            gen.throw(RuntimeError("simulated request error"))
        except RuntimeError:
            pass

        mock_session.close.assert_called_once()
