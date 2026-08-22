"""Create/upgrade the per-account databases declared in HAB7BOT_ACCOUNTS.

Each web-only member account (see app/auth.py::parse_accounts) gets its own
private compass_acct_<name>.db. Run this after every deploy, alongside
`alembic upgrade head` for the main DB — a missing account DB is created
with the full schema; existing ones are upgraded in place. Accounts start
empty: onboarding happens through the web app itself.

Run:  python -m scripts.migrate_accounts
"""
import os

from alembic.config import Config

from alembic import command
from app.auth import parse_accounts
from app.config import BACKEND_DIR
from app.db import account_database_url


def migrate_all() -> list[str]:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))

    migrated = []
    for name in parse_accounts():
        os.environ["ALEMBIC_DATABASE_URL"] = account_database_url(name)
        try:
            command.upgrade(cfg, "head")
        finally:
            del os.environ["ALEMBIC_DATABASE_URL"]
        migrated.append(name)
        print(f"  ✓ {name} → {account_database_url(name)}")
    return migrated


def main() -> None:
    migrated = migrate_all()
    if migrated:
        print(f"Migrated {len(migrated)} account database(s).")
    else:
        print("No accounts declared in HAB7BOT_ACCOUNTS — nothing to do.")


if __name__ == "__main__":
    main()
