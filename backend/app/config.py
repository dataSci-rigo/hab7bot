from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    app_password: str = "changeme"
    # Typing this into the login form starts a read-only demo session served
    # from the seeded showcase DB. Deliberately not a secret — the login page
    # prints it as a hint.
    demo_password: str = "demo"
    session_secret: str = "changeme"
    web_origin: str = "http://localhost:3000"

    database_url: str = f"sqlite:///{BACKEND_DIR / 'data' / 'compass.db'}"
    # Read-only guest sessions are served from this separate showcase DB
    # (seeded by scripts/seed_demo.py) so guests never see the real planner.
    demo_database_url: str = f"sqlite:///{BACKEND_DIR / 'data' / 'compass_demo.db'}"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_model_fast: str = "claude-haiku-4-5"

    # Named with a HAB7BOT_ prefix (not the plain TELEGRAM_* you'd expect) —
    # this .env lives inside a shared env_sync.py master alongside several
    # other Telegram bots' credentials; a generic name risks visual mix-ups
    # even though env_sync's per-project sections keep the values themselves
    # from actually colliding.
    telegram_bot_token: str = Field(default="", validation_alias="HAB7BOT_TELEGRAM_TOKEN")
    telegram_allowed_user_id: int = Field(
        default=0, validation_alias="HAB7BOT_ALLOWED_USER_ID"
    )

    # Shared secret for bot-to-bot capture calls (brain-dump). Empty = the
    # X-Api-Key path is disabled and only session-cookie auth works.
    internal_api_key: str = Field(default="", validation_alias="HAB7BOT_INTERNAL_API_KEY")

    week_start_day: str = "monday"

    # Same OAuth client already set up for semantic_task_manager (project
    # "humorbot") — reused rather than registering a new Google Cloud app.
    _humorbot_client_secret = (
        "client_secret_994331043279-p0c58fgvb760e5b37p90qgp35asn4e5j"
        ".apps.googleusercontent.com.json"
    )
    google_client_secret_path: str = str(Path.home() / "Documents" / _humorbot_client_secret)
    google_token_path: str = str(BACKEND_DIR / "data" / "google_token.json")

    # Linked from the Sunday planning prompt so the user can finish planning
    # visually — a deployment-level constant (dev vs. VM URL), not
    # user-editable data, so it lives here rather than on AppSettings.
    web_app_url: str = "http://localhost:3000"


settings = Settings()
