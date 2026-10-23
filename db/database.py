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

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base

DEFAULT_DB_PATH = Path("bastion_command.db")

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _sync_schema(engine: Engine) -> None:
    """Add any columns that exist on the models but not yet in the database file.

    We only ever add nullable columns to existing tables (additive-only schema
    changes), so a simple ``ALTER TABLE ... ADD COLUMN`` per missing column is
    enough — this avoids "no such column" errors on a database file created
    before a field was added, without needing a full migration framework.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue  # brand new table — create_all already created it with all columns
            existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue
                col_type = column.type.compile(engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'))


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> Engine:
    """Create the engine, session factory, and any missing tables/columns.

    Safe to call once at application startup. Existing tables are left
    untouched by create_all (it only creates tables that don't already exist),
    so a follow-up schema sync adds any columns a new model field introduced.
    """
    global _engine, _SessionLocal

    _engine = create_engine(f"sqlite:///{db_path}")
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)
    _sync_schema(_engine)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database not initialized — call init_db() first.")
    return _engine


def close_db() -> None:
    """Dispose the engine, releasing file handles/connections.

    Call this before re-encrypting an encrypted database's working copy on
    app shutdown — SQLite must not have open connections while its file is
    read back for encryption.
    """
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


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
