"""Thin time seam so scheduled-job logic can be tested with a simulated
clock (monkeypatch these functions) instead of freezing real time.
"""
from datetime import date, datetime

from app.services.iso_week import iso_week_string


def now() -> datetime:
    return datetime.now()


def today() -> date:
    return now().date()


def current_iso_week() -> str:
    return iso_week_string(today())
