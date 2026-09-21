# Ref: BL-O1-001 | Skill: K-014 | Fase: F6
"""Database engine and session factory."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


def _build_engine():
    settings = get_settings()
    url = settings.database_url
    connect_args = {}
    engine_kwargs: dict = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        engine_kwargs["connect_args"] = connect_args
        if ":memory:" in url:
            from sqlalchemy.pool import StaticPool

            engine_kwargs["poolclass"] = StaticPool
            engine_kwargs.pop("pool_pre_ping", None)
    else:
        engine_kwargs["connect_args"] = connect_args

    eng = create_engine(url, **engine_kwargs)

    if url.startswith("sqlite"):

        @event.listens_for(eng, "connect")
        def _fk_pragma(dbapi_connection, _connection_record):  # noqa: ANN001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return eng


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_engine() -> None:
    """Rebuild engine after settings cache clear (tests)."""
    global engine, SessionLocal
    engine = _build_engine()
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
