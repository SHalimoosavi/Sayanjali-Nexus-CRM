"""
Database engine and session management.

Uses SQLAlchemy 2.0 style. `connect_args` check_same_thread is only applied
for SQLite; when DATABASE_URL becomes a postgres:// URL this branch is skipped
automatically, so no migration code is needed for the engine layer.
"""
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Ensure the local data directory exists for the SQLite file.
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if db_path not in (":memory:",):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
