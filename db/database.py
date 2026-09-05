"""
Database Engine & Session Setup (Viper)
=========================================

Local SQLite database, no server. The database file lives alongside the app
(e.g. `bastion_command.db` in the current working directory) unless a path is
supplied explicitly.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base

DEFAULT_DB_PATH = Path("bastion_command.db")

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> Engine:
    """Create the engine, session factory, and any missing tables.

    Safe to call once at application startup. Existing tables are left
    untouched (create_all only creates tables that don't already exist).
    """
    global _engine, _SessionLocal

    _engine = create_engine(f"sqlite:///{db_path}")
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database not initialized — call init_db() first.")
    return _engine


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a SQLAlchemy session, committing on success and rolling back on error."""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized — call init_db() first.")

    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
