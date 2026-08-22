from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Guest sessions read a separate, seeded showcase database (see
# scripts/seed_demo.py) — never the owner's real planner. Created lazily so
# the bot worker and tests, which only use SessionLocal, never touch it.
_demo_engine: Engine | None = None
_DemoSessionLocal: sessionmaker | None = None


def _demo_session() -> Session:
    global _demo_engine, _DemoSessionLocal
    if _DemoSessionLocal is None:
        _demo_engine = create_engine(
            settings.demo_database_url, connect_args={"check_same_thread": False}
        )
        _DemoSessionLocal = sessionmaker(
            bind=_demo_engine, autoflush=False, autocommit=False
        )
    return _DemoSessionLocal()


class Base(DeclarativeBase):
    pass


def get_db(request: Request = None) -> Generator[Session, None, None]:
    # Imported here, not at module top: app.auth imports app.config only,
    # but keeping db.py free of an auth import at import time avoids any
    # circular-import risk for non-request users of this module (bot, tests).
    from app.auth import ROLE_GUEST, request_session_role

    is_guest = request is not None and request_session_role(request) == ROLE_GUEST
    db = _demo_session() if is_guest else SessionLocal()
    try:
        yield db
    finally:
        db.close()
