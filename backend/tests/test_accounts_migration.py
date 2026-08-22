import sqlite3

import pytest

from app.config import settings


def test_migrate_accounts_creates_dbs_at_head(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.auth import parse_accounts

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/compass.db")
    monkeypatch.setattr(settings, "accounts", "testacct:pw-test")
    parse_accounts.cache_clear()
    try:
        from scripts.migrate_accounts import migrate_all

        migrated = migrate_all()
    finally:
        parse_accounts.cache_clear()

    assert migrated == ["testacct"]
    db_file = tmp_path / "compass_acct_testacct.db"
    assert db_file.exists()

    con = sqlite3.connect(db_file)
    tables = {
        r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    con.close()
    assert "alembic_version" in tables
    assert {"tasks", "roles", "weekly_reviews", "settings"} <= tables
