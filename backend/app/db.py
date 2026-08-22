from collections.abc import Generator
from pathlib import Path

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

# Non-owner sessions are served from separate SQLite files, created lazily
# so the bot worker and tests, which only use SessionLocal, never touch
# them: guests get the seeded showcase DB (scripts/seed_demo.py), members
# each get their own private compass_acct_<name>.db. Names reaching
# account_database_url are already validated by app/auth.py::parse_accounts
# (^[a-z0-9_-]{1,32}$) — never raw user input.
_extra_sessionmakers: dict[str, sessionmaker] = {}


def account_database_url(account: str) -> str:
    data_dir = Path(settings.database_url.removeprefix("sqlite:///")).parent
    return f"sqlite:///{data_dir / f'compass_acct_{account}.db'}"


def _extra_session(url: str) -> Session:
    maker = _extra_sessionmakers.get(url)
    if maker is None:
        extra_engine = create_engine(url, connect_args={"check_same_thread": False})
        maker = sessionmaker(bind=extra_engine, autoflush=False, autocommit=False)
        _extra_sessionmakers[url] = maker
    return maker()


def _demo_session() -> Session:
    return _extra_session(settings.demo_database_url)


def _account_session(account: str) -> Session:
    return _extra_session(account_database_url(account))


class Base(DeclarativeBase):
    pass


def get_db(request: Request = None) -> Generator[Session, None, None]:
    # Imported here, not at module top: app.auth imports app.config only,
    # but keeping db.py free of an auth import at import time avoids any
    # circular-import risk for non-request users of this module (bot, tests).
    from app.auth import ROLE_GUEST, ROLE_MEMBER, request_session_identity

    identity = request_session_identity(request) if request is not None else None
    if identity is not None and identity[0] == ROLE_GUEST:
        db = _demo_session()
    elif identity is not None and identity[0] == ROLE_MEMBER:
        db = _account_session(identity[1])
    else:
        # owner, API-key callers (no cookie), and non-request users
        db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
