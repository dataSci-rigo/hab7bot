from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    app_password: str = "changeme"
    session_secret: str = "changeme"

    database_url: str = f"sqlite:///{BACKEND_DIR / 'data' / 'compass.db'}"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_model_fast: str = "claude-haiku-4-5"

    telegram_bot_token: str = ""
    telegram_allowed_user_id: int = 0

    week_start_day: str = "monday"


settings = Settings()
