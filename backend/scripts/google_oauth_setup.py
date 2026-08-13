#!/usr/bin/env python3
"""One-time local authorization for Google Calendar + Tasks sync.

Run this yourself in a terminal with a browser available (not headless —
this can't run on the VM). It opens a browser window, you approve access,
and it saves a refresh token to GOOGLE_TOKEN_PATH (default
backend/data/google_token.json), which the api/bot processes then use to
authenticate headlessly from then on.

Run: python -m scripts.google_oauth_setup
"""
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import settings
from app.integrations.google.auth import SCOPES


def main() -> None:
    flow = InstalledAppFlow.from_client_secrets_file(
        settings.google_client_secret_path, SCOPES
    )
    creds = flow.run_local_server(port=0)

    token_path = Path(settings.google_token_path)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    print(f"Saved token to {token_path}")


if __name__ == "__main__":
    main()
