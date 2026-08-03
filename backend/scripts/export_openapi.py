"""Dump the FastAPI app's OpenAPI schema to backend/openapi.json.

Run: python -m scripts.export_openapi
"""
import json
from pathlib import Path

from app.main import app

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def export() -> None:
    OUTPUT_PATH.write_text(json.dumps(app.openapi(), indent=2))
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    export()
